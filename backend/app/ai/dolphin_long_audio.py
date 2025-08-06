import os
import logging
from typing import Dict
import dolphin
import gc

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DialogueTranscriptionEngine:
    """Simple dialogue transcription engine"""
    
    def __init__(self, model_name="small", model_path="./models", device="cuda"):
        """Initialize transcription engine"""
        self.model_name = model_name
        self.model_path = model_path
        self.device = device
        self.model = None
        
        logger.info("初始化 Dolphin 語音服務")
        try:
            os.makedirs(model_path, exist_ok=True)
            self.model = dolphin.load_model(
                model_name=model_name,
                model_dir=model_path,
                device=device
            )
            logger.info("Dolphin 語音服務初始化成功")
        except Exception as e:
            logger.error(f"Dolphin 語音服務初始化失敗: {e}")
            raise
    
    def process_audio(self, audio_path: str) -> Dict:
        """Process audio file sequentially without threading - single-threaded processing"""
        waveform = None
        try:
            logger.info(f"開始單線程處理音頻: {audio_path}")
            
            # Load audio once at the beginning
            waveform = dolphin.load_audio(audio_path)
            sample_rate = 16000
            total_duration = len(waveform) / sample_rate
            
            logger.info(f"音頻載入完成，總時長: {total_duration:.2f}秒")
            
            transcribed_segments = []
            chunk_length = 30.0  # 30 seconds
            overlap = 0.1        # 0.1 seconds overlap
            start_time = 0.0
            segment_id = 0
            
            # Process audio in sequential chunks
            while start_time < total_duration:
                end_time = min(start_time + chunk_length, total_duration)
                logger.info(f"順序處理段落 {segment_id + 1}/{int(total_duration/chunk_length)+1} ({start_time:.1f}s - {end_time:.1f}s)")
                
                # Extract audio chunk
                start_sample = int(start_time * sample_rate)
                end_sample = int(end_time * sample_rate)
                audio_chunk = waveform[start_sample:end_sample]
                
                # Single-threaded transcription
                try:
                    result = self.model(audio_chunk, lang_sym="zh", region_sym="TW")
                    text = result.text.strip() if result and hasattr(result, 'text') else ''
                    
                    if text:
                        transcribed_segments.append({
                            'text': text,
                            'start': start_time,
                            'end': end_time,
                            'confidence': getattr(result, 'confidence', 0.0)
                        })
                        logger.info(f"段落 {segment_id + 1} 轉錄完成: {len(text)} 字符")
                    
                except Exception as e:
                    logger.warning(f"段落 {segment_id + 1} 處理失敗: {e}")
                    # Continue with next segment
                
                # Force garbage collection after each segment
                del audio_chunk
                gc.collect()
                
                # Move to next segment
                if end_time >= total_duration:
                    break
                start_time = end_time - overlap
                segment_id += 1
            
            # Compose final result
            full_text = " ".join([seg['text'] for seg in transcribed_segments])
            
            result = {
                'text': full_text,
                'segments': transcribed_segments,
                'duration': total_duration,
                'language': "zh",
                'model': self.model_name
            }
            
            logger.info(f"單線程轉錄完成: {len(transcribed_segments)} 段落, 文字總長度: {len(full_text)} 字符")
            return result
            
        except Exception as e:
            logger.error(f"音頻處理失敗: {e}")
            return {
                'text': '',
                'segments': [],
                'duration': 0,
                'language': "zh",
                'model': self.model_name,
                'error': str(e)
            }
        finally:
            # Clean up resources
            if waveform is not None:
                del waveform
            gc.collect()
            logger.info("音頻處理資源已清理")