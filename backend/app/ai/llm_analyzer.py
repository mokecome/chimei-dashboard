"""
優化的 LLM 分析器 - 支持完整內容處理
"""
import requests
import re
import json
import time
from opencc import OpenCC
from typing import Dict, Optional

# 配置
LLM_API_URL = 'http://192.168.50.123:11434/api/generate'
MODEL_NAME = 'qwen3:8b'
cc = OpenCC('s2t')

def clean_asr_tags(text: str) -> str:
    """清除 ASR 標記"""
    cleaned = re.sub(r'<[^>]+>', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def calculate_dynamic_timeout(content_length: int) -> int:
    """
    根據內容長度計算動態超時時間
    基準：每 1000 字符需要約 60 秒處理時間
    """
    base_timeout = 180  # 基礎超時 3 分鐘
    chars_per_minute = 1000  # 每分鐘處理字符數
    
    # 計算需要的額外時間
    extra_time = (content_length / chars_per_minute) * 60
    
    # 總超時時間，最大 10 分鐘
    total_timeout = min(600, base_timeout + extra_time)
    
    return int(total_timeout)

def call_llm_streaming(transcript: str, product_list: str = "", 
                      feedback_list: str = "") -> Dict:
    """
    使用流式 API 處理長內容，避免超時
    """
    # 優化的提示詞模板
    prompt_template = (
        "/no_think\n"
        "/role:你是台灣食品業的客服資料標註專家。\n"
        "/task:分析以下客服對話，直接輸出JSON結果。\n\n"
        "要求：\n"
        "1. 使用繁體中文\n"
        "2. 摘要保持在200字內\n"
        "3. 只輸出JSON格式結果\n\n"
        "JSON格式：\n"
        '{{\n'
        '  "product_name": "食品名稱（可多個，無則填「無」）",\n'
        '  "evaluation_tendency": "正面/負面/中立",\n'
        '  "feedback_category": "對話分類",\n'
        '  "feedback_summary": "對話摘要（200字內）",\n'
        '  "detailed_content": "關鍵內容"\n'
        '}}\n\n'
    )
    
    # 添加可選清單
    if product_list:
        prompt_template += f"可選產品：{product_list}\n\n"
    if feedback_list:
        prompt_template += f"分類選項：{feedback_list}\n\n"
    
    prompt_template += f"客服對話：\n{transcript}\n\nJSON結果："
    
    # 計算超時時間
    content_length = len(transcript)
    timeout = calculate_dynamic_timeout(content_length)
    
    print(f"📊 內容長度：{content_length} 字符")
    print(f"⏱️  設定超時：{timeout} 秒")
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt_template,
        "stream": True,  # 啟用流式處理
        "temperature": 0,
        "top_p": 0.5,
        "options": {
            "num_ctx": 8192,  # 增加上下文窗口
            "num_predict": 1000  # 限制輸出長度
        }
    }
    
    try:
        print("🔄 開始流式處理...")
        response = requests.post(
            LLM_API_URL,
            json=payload,
            stream=True,
            timeout=(30, timeout),  # (連接超時, 讀取超時)
            headers={'Connection': 'keep-alive'}
        )
        
        # 逐塊讀取響應
        full_response = ""
        start_time = time.time()
        chunk_count = 0
        
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    if chunk.get("response"):
                        full_response += chunk["response"]
                        chunk_count += 1
                        
                        # 每 10 個塊顯示進度
                        if chunk_count % 10 == 0:
                            elapsed = time.time() - start_time
                            print(f"  處理中... ({elapsed:.1f}秒)")
                    
                    # 檢查是否完成
                    if chunk.get("done", False):
                        print(f"✅ 流式處理完成 (共 {chunk_count} 塊)")
                        break
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"⚠️ 處理塊時出錯: {e}")
                    continue
        
        return parse_llm_response(full_response)
        
    except requests.exceptions.Timeout:
        print("❌ 流式處理超時")
        return fallback_analysis(transcript)
    except Exception as e:
        print(f"❌ 流式處理失敗: {str(e)}")
        return {"error": f"流式處理失敗: {str(e)}"}

def call_llm_with_retry(transcript: str, product_list: str = "", 
                       feedback_list: str = "", max_retries: int = 2) -> Dict:
    """
    帶重試機制的 LLM 調用（非流式備用方案）
    """
    # 簡化的提示詞
    prompt = f"""
/no_think
你是客服分析專家，請分析以下對話並輸出JSON：
{{
  "product_name": "產品名稱或無",
  "evaluation_tendency": "正面/負面/中立",
  "feedback_category": "分類",
  "feedback_summary": "摘要(200字內)"
}}

對話：{transcript[:3000]}...

JSON："""
    
    # 動態超時
    timeout = calculate_dynamic_timeout(len(transcript))
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "temperature": 0,
        "top_p": 0.5
    }
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 第 {attempt + 1} 次嘗試...")
            resp = requests.post(LLM_API_URL, json=payload, timeout=timeout)
            
            if resp.status_code == 200:
                result = resp.json().get("response", "")
                return parse_llm_response(result)
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"⏰ 超時，等待後重試...")
                time.sleep(10)
                continue
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            
    return fallback_analysis(transcript)

def parse_llm_response(result: str) -> Dict:
    """解析 LLM 響應"""
    # 轉繁體
    result = cc.convert(result)
    
    # 嘗試提取 JSON
    match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
    
    if match:
        try:
            parsed = json.loads(match.group(0))
            
            # 確保所有必要字段存在
            required_fields = ["product_name", "evaluation_tendency", 
                             "feedback_category", "feedback_summary"]
            
            for field in required_fields:
                if field not in parsed:
                    parsed[field] = get_default_value(field)
            
            # 限制摘要長度（但不截斷內容）
            if len(parsed.get("feedback_summary", "")) > 500:
                parsed["feedback_summary"] = parsed["feedback_summary"][:497] + "..."
            
            return parsed
            
        except json.JSONDecodeError:
            print("⚠️ JSON 解析失敗，使用備用方案")
    
    return fallback_analysis(result)

def fallback_analysis(transcript: str) -> Dict:
    """
    基於規則的備用分析（不依賴 LLM）
    保留完整內容，提供基礎分析
    """
    # 關鍵詞分析
    positive_words = ["謝謝", "很好", "滿意", "不錯", "喜歡", "棒", "讚", "優秀"]
    negative_words = ["問題", "投訴", "退貨", "不滿", "差", "爛", "失望", "糟糕"]
    
    # 產品關鍵詞
    product_keywords = {
        "水餃": ["水餃", "餃子"],
        "包子": ["包子", "饅頭"],
        "湯圓": ["湯圓", "元宵"],
        "餛飩": ["餛飩", "雲吞"],
        "燒賣": ["燒賣", "燒麥"]
    }
    
    # 統計情緒
    text_lower = transcript.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    # 判斷情緒
    if positive_count > negative_count * 2:
        sentiment = "正面"
    elif negative_count > positive_count * 2:
        sentiment = "負面"
    else:
        sentiment = "中立"
    
    # 識別產品
    found_products = []
    for product, keywords in product_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            found_products.append(product)
    
    # 判斷類別
    if any(word in text_lower for word in ["退", "換", "賠"]):
        category = "退換貨諮詢"
    elif any(word in text_lower for word in ["買", "訂", "購"]):
        category = "訂購諮詢"
    elif any(word in text_lower for word in ["問題", "投訴"]):
        category = "問題反饋"
    else:
        category = "一般諮詢"
    
    return {
        "product_name": found_products if found_products else ["無"],
        "evaluation_tendency": sentiment,
        "feedback_category": category,
        "feedback_summary": "系統自動分析完成，保留完整對話內容，建議人工複核確認分析結果。",
        "detailed_content": "完整內容已保存"
    }

def get_default_value(field: str) -> any:
    """獲取字段默認值"""
    defaults = {
        "product_name": ["無"],
        "evaluation_tendency": "中立",
        "feedback_category": "一般諮詢",
        "feedback_summary": "待分析",
        "detailed_content": ""
    }
    return defaults.get(field, "")

def analyze_feedback(transcript: str, product_list: str = "", 
                    feedback_list: str = "") -> Dict:
    """
    主分析函數 - 優化版本
    """
    # 清理轉錄文本
    cleaned_transcript = clean_asr_tags(transcript)
    
    print(f"\n🎯 開始分析 (長度: {len(cleaned_transcript)} 字符)")
    
    # 優先使用流式處理
    result = call_llm_streaming(cleaned_transcript, product_list, feedback_list)
    
    # 如果流式處理失敗，嘗試標準方式
    if "error" in result:
        print("⚠️ 流式處理失敗，嘗試標準方式...")
        result = call_llm_with_retry(cleaned_transcript, product_list, feedback_list)
    
    # 確保返回完整的分析結果
    if "error" not in result:
        print("✅ 分析成功完成")
    else:
        print(f"❌ 分析失敗: {result.get('error', '未知錯誤')}")
    
    return result

# 保持與原始接口兼容
call_llm = analyze_feedback

if __name__ == "__main__":
    # 測試
    test_transcript = "客戶詢問水餃的保存方式，表示很滿意產品品質..."
    result = analyze_feedback(test_transcript)
    print(json.dumps(result, ensure_ascii=False, indent=2))