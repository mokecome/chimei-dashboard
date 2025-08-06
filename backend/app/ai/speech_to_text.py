import logging
from .dolphin_long_audio import DialogueTranscriptionEngine

logger = logging.getLogger(__name__)

class SpeechService:
    def __init__(self):
        logger.info("初始化 Dolphin 語音服務")
        try:
            self.engine = DialogueTranscriptionEngine()
            logger.info("Dolphin 語音服務初始化成功")
        except Exception as e:
            logger.error(f"Dolphin 語音服務初始化失敗: {e}")
            self.engine = None

    def speech_to_text(self, file_path: str) -> str:
        """
        語音檔轉文字，回傳全部內容（合併段落）
        
        Args:
            file_path: 檔案路徑（支援 WAV, MP3, TXT）
            
        Returns:
            轉錄的文字內容
        """
        try:
            if file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            
            result = self.engine.process_audio(file_path)
            return result.get("text", "")
            
        except Exception as e:
            logger.error(f"語音轉文字失敗: {e}")
            return ""

    def get_audio_duration(self, file_path: str) -> float:
        """
        獲取音頻檔案的時長
        
        Args:
            file_path: 音頻檔案路徑
            
        Returns:
            音頻時長（秒）
        """
        try:
            if self.engine:
                return self.engine.get_audio_duration(file_path)
            else:
                logger.warning("語音引擎未初始化")
                return 0.0
        except Exception as e:
            logger.error(f"無法計算音頻時長: {e}")
            return 0.0

# Create singleton instance for import
speech_service = SpeechService()

