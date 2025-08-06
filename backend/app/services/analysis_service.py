"""
Analysis service for AI analysis operations.
Single-threaded processing to avoid resource competition.
"""
import json
import logging
import time
import psutil
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from ..repositories.analysis import AnalysisRepository
from ..repositories.file import FileRepository
from ..repositories.label import LabelRepository
from ..models.analysis import VoiceAnalysis, SentimentType
from ..models.file import FileStatus
from ..schemas.analysis import AnalysisCreate, AnalysisFilterParams
from ..schemas.common import PaginationParams, PaginatedResponse
from ..ai.speech_to_text import speech_service
from ..ai.llm_analyzer import analyze_feedback

logger = logging.getLogger(__name__)


class AnalysisService:
    """AI analysis service with single-threaded processing."""
    
    # Class-level processing flag to prevent concurrent analysis
    _processing = False
    _processing_file_id = None
    
    def __init__(self, db: Session):
        self.db = db
        self.analysis_repo = AnalysisRepository(db)
        self.file_repo = FileRepository(db)
        self.label_repo = LabelRepository(db)
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage before starting analysis."""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        
        return {
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'cpu_percent': cpu_percent,
            'disk_free_gb': disk.free / (1024**3),
            'system_healthy': (
                memory.percent < 85 and  # Memory usage < 85%
                cpu_percent < 90 and     # CPU usage < 90%
                disk.free > 1024**3     # At least 1GB free disk
            )
        }
    
    def _log_resource_usage(self, stage: str):
        """Log current resource usage."""
        resources = self._check_system_resources()
        logger.info(f"[{stage}] 記憶體: {resources['memory_percent']:.1f}%, "
                   f"CPU: {resources['cpu_percent']:.1f}%, "
                   f"可用記憶體: {resources['memory_available_gb']:.1f}GB")
    
    def get_analysis(self, analysis_id: str) -> Optional[VoiceAnalysis]:
        """Get analysis by ID."""
        return self.analysis_repo.get_with_file_info(analysis_id)
    
    def get_analysis_by_file_id(self, file_id: str) -> Optional[VoiceAnalysis]:
        """Get analysis by file ID."""
        return self.analysis_repo.get_by_file_id(file_id)
    
    def process_file_analysis(self, file_id: str) -> Dict[str, Any]:
        """Process file analysis workflow with single-threaded control."""
        # Check if another analysis is already in progress
        if AnalysisService._processing:
            logger.warning(f"Analysis already in progress for file {AnalysisService._processing_file_id}, queuing file {file_id}")
            return {"error": "Another analysis is in progress. Please try again later."}
        
        # Check system resources before starting
        resources = self._check_system_resources()
        if not resources['system_healthy']:
            logger.error(f"System resources insufficient for analysis: {resources}")
            return {"error": f"System resources insufficient. Memory: {resources['memory_percent']:.1f}%, CPU: {resources['cpu_percent']:.1f}%, Disk: {resources['disk_free_gb']:.1f}GB"}
        
        try:
            # Set processing flag
            AnalysisService._processing = True
            AnalysisService._processing_file_id = file_id
            
            # Log resource usage at start
            self._log_resource_usage("Start")
            
            # Get file
            file_obj = self.file_repo.get(file_id)
            if not file_obj:
                return {"error": "File not found"}
            
            # Check if analysis already exists and file is completed
            existing_analysis = self.analysis_repo.get_by_file_id(file_id)
            if existing_analysis and file_obj.status == FileStatus.COMPLETED:
                return {"error": "Analysis already exists for this file"}
            
            # Update file status to ANALYZING (分析中)
            self.file_repo.update_status(file_id, FileStatus.ANALYZING)
            logger.info(f"Started single-threaded analysis for file {file_id}")
            
            # Convert speech to text
            try:
                self._log_resource_usage("Before Speech-to-Text")
                transcript = speech_service.speech_to_text(file_obj.file_path)
                if not transcript:
                    # Set to FAILED status for retry option
                    self.file_repo.update_status(file_id, FileStatus.FAILED)
                    logger.error(f"Speech-to-text returned empty transcript for file {file_id}")
                    return {"error": "Failed to transcribe audio - empty result"}
                self._log_resource_usage("After Speech-to-Text")
                logger.info(f"Successfully transcribed file {file_id}, transcript length: {len(transcript)}")
            except Exception as e:
                logger.error(f"Speech-to-text failed for file {file_id}: {str(e)}")
                self.file_repo.update_status(file_id, FileStatus.FAILED)
                return {"error": f"Speech-to-text processing failed: {str(e)}"}
            
            # Get labels for analysis context
            product_labels = self.label_repo.get_product_labels(active_only=True, limit=1000)
            feedback_categories = self.label_repo.get_feedback_categories(active_only=True, limit=1000)
            
            product_list = "\n".join([label.name for label in product_labels])
            feedback_list = "\n".join([category.name for category in feedback_categories])
            
            # Analyze content with LLM
            try:
                self._log_resource_usage("Before LLM Analysis")
                analysis_result = analyze_feedback(transcript, product_list, feedback_list)
                
                if "error" in analysis_result:
                    # Set to FAILED status for retry option
                    self.file_repo.update_status(file_id, FileStatus.FAILED)
                    logger.error(f"LLM analysis returned error for file {file_id}: {analysis_result['error']}")
                    return {"error": f"Analysis failed: {analysis_result['error']}"}
                
                self._log_resource_usage("After LLM Analysis")
                logger.info(f"Successfully analyzed file {file_id}")
            except Exception as e:
                logger.error(f"LLM analysis exception for file {file_id}: {str(e)}")
                self.file_repo.update_status(file_id, FileStatus.FAILED)
                return {"error": f"LLM analysis failed: {str(e)}"}
            
            # Parse product names
            product_names = []
            if analysis_result.get("product_name"):
                products = analysis_result["product_name"].replace("、", ",").replace("，", ",").split(",")
                product_names = [p.strip() for p in products if p.strip() and p.strip() != "無"]
            
            # Parse feedback category - handle both string and list formats
            feedback_category = analysis_result.get("feedback_category", "")
            if isinstance(feedback_category, list):
                # Convert list to comma-separated string
                feedback_category = ", ".join([str(item).strip() for item in feedback_category if str(item).strip()])
            elif not isinstance(feedback_category, str):
                # Convert any non-string to string
                feedback_category = str(feedback_category)
            
            # Map Chinese sentiment to English enum
            sentiment_mapping = {
                "正面": SentimentType.POSITIVE,
                "positive": SentimentType.POSITIVE,
                "負面": SentimentType.NEGATIVE, 
                "negative": SentimentType.NEGATIVE,
                "中立": SentimentType.NEUTRAL,
                "中性": SentimentType.NEUTRAL,
                "neutral": SentimentType.NEUTRAL
            }
            
            raw_sentiment = analysis_result.get("evaluation_tendency", "中立").lower()
            sentiment = sentiment_mapping.get(raw_sentiment, SentimentType.NEUTRAL)
            
            # Create or update analysis record
            analysis_data = {
                "file_id": file_id,
                "transcript": transcript,
                "sentiment": sentiment,
                "feedback_category": feedback_category,
                "feedback_summary": analysis_result.get("feedback_summary", ""),
                "product_names": json.dumps(product_names, ensure_ascii=False) if product_names else None
            }
            
            # Save analysis results with transaction safety
            try:
                if existing_analysis:
                    # Update existing analysis
                    for key, value in analysis_data.items():
                        if key != "file_id":  # Don't update file_id
                            setattr(existing_analysis, key, value)
                    self.db.commit()
                    analysis = existing_analysis
                    logger.info(f"Updated existing analysis for file {file_id}")
                else:
                    # Create new analysis
                    analysis = self.analysis_repo.create(analysis_data)
                    logger.info(f"Created new analysis for file {file_id}")
                
                # Update file status to COMPLETED (分析完成)
                self.file_repo.update_status(file_id, FileStatus.COMPLETED)
                logger.info(f"Completed analysis for file {file_id}")
                
            except Exception as e:
                logger.error(f"Database operation failed for file {file_id}: {str(e)}")
                # Try to rollback
                try:
                    self.db.rollback()
                except:
                    pass
                self.file_repo.update_status(file_id, FileStatus.FAILED)
                return {"error": f"Failed to save analysis results: {str(e)}"}
            
            return {
                "success": True,
                "analysis_id": analysis.id,
                "message": "Analysis completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Analysis failed for file {file_id}: {e}")
            # Ensure file status is updated to FAILED for retry option
            try:
                self.file_repo.update_status(file_id, FileStatus.FAILED)
            except Exception as status_error:
                logger.error(f"Failed to update file status to FAILED for {file_id}: {status_error}")
            return {"error": f"Analysis processing failed: {str(e)}"}
        finally:
            # Always clear processing flag and log final resource usage
            try:
                self._log_resource_usage("End")
            except:
                pass  # Don't let logging errors prevent cleanup
            
            AnalysisService._processing = False
            AnalysisService._processing_file_id = None
            logger.info(f"Released processing lock for file {file_id}")
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics for dashboard."""
        return {
            "total_analyses": self.analysis_repo.count(),
            "sentiment_distribution": self.analysis_repo.get_sentiment_distribution(),
            "product_distribution": self.analysis_repo.get_product_distribution(limit=10),
            "category_distribution": self.analysis_repo.get_category_distribution(limit=10),
            "daily_trend": self.analysis_repo.get_daily_trend(days=30),
            "recent_analyses": self.analysis_repo.get_recent_analyses(limit=10)
        }