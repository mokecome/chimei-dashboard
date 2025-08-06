"""
Statistics service for dashboard analytics and reporting.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text

from ..repositories.user import UserRepository
from ..repositories.file import FileRepository
from ..repositories.analysis import AnalysisRepository
from ..repositories.label import LabelRepository
from ..models.user import User, UserRole
from ..models.file import VoiceFile, FileStatus, FileFormat
from ..models.analysis import VoiceAnalysis, SentimentType
from ..models.label import ProductLabel, FeedbackCategory

logger = logging.getLogger(__name__)


class StatisticsService:
    """Statistics and analytics service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.file_repo = FileRepository(db)
        self.analysis_repo = AnalysisRepository(db)
        self.label_repo = LabelRepository(db)
    
    def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get overall dashboard statistics."""
        try:
            # Basic counts
            total_users = self.user_repo.count()
            total_files = self.file_repo.count()
            total_analyses = self.analysis_repo.count()
            total_labels = self.label_repo.get_product_labels_count()
            
            # File status distribution
            file_status_stats = self._get_file_status_distribution()
            
            # Recent activity (last 30 days)
            recent_activity = self._get_recent_activity(days=30)
            
            # Processing statistics
            processing_stats = self._get_processing_statistics()
            
            # Sentiment distribution
            sentiment_stats = self._get_sentiment_distribution()
            
            return {
                "overview": {
                    "total_users": total_users,
                    "total_files": total_files,
                    "total_analyses": total_analyses,
                    "total_labels": total_labels
                },
                "file_status": file_status_stats,
                "recent_activity": recent_activity,
                "processing_stats": processing_stats,
                "sentiment_distribution": sentiment_stats,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            return self._empty_dashboard_stats()
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user-related statistics."""
        try:
            # User count by role
            user_role_stats = {}
            for role in UserRole:
                count = self.db.query(User).filter(User.role == role).count()
                user_role_stats[role.value] = count
            
            # Active vs inactive users
            active_users = self.db.query(User).filter(User.is_active == True).count()
            inactive_users = self.db.query(User).filter(User.is_active == False).count()
            
            # Registration trend (last 12 months)
            registration_trend = self._get_registration_trend()
            
            # Most active users (by file uploads)
            most_active_users = self._get_most_active_users()
            
            return {
                "role_distribution": user_role_stats,
                "activity_status": {
                    "active": active_users,
                    "inactive": inactive_users
                },
                "registration_trend": registration_trend,
                "most_active_users": most_active_users
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {"error": f"Failed to get user statistics: {str(e)}"}
    
    def get_file_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get file-related statistics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # File format distribution
            format_stats = {}
            for format in FileFormat:
                count = self.db.query(VoiceFile).filter(VoiceFile.file_format == format).count()
                format_stats[format.value] = count
            
            # File size statistics
            file_size_stats = self._get_file_size_statistics()
            
            # Upload trend
            upload_trend = self._get_upload_trend(days=days)
            
            # Processing success rate
            success_rate = self._get_processing_success_rate()
            
            # Average processing time
            avg_processing_time = self._get_average_processing_time()
            
            return {
                "format_distribution": format_stats,
                "size_statistics": file_size_stats,
                "upload_trend": upload_trend,
                "processing_metrics": {
                    "success_rate": success_rate,
                    "average_processing_time": avg_processing_time
                },
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting file statistics: {e}")
            return {"error": f"Failed to get file statistics: {str(e)}"}
    
    def get_analysis_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get analysis-related statistics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Sentiment distribution over time
            sentiment_trend = self._get_sentiment_trend(days=days)
            
            # Top products mentioned
            top_products = self._get_top_mentioned_products(limit=10)
            
            # Top feedback categories
            top_categories = self._get_top_feedback_categories(limit=10)
            
            # Analysis quality metrics
            quality_metrics = self._get_analysis_quality_metrics()
            
            # Daily analysis volume
            daily_volume = self._get_daily_analysis_volume(days=days)
            
            return {
                "sentiment_trend": sentiment_trend,
                "top_products": top_products,
                "top_categories": top_categories,
                "quality_metrics": quality_metrics,
                "daily_volume": daily_volume,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis statistics: {e}")
            return {"error": f"Failed to get analysis statistics: {str(e)}"}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        try:
            # Processing time statistics
            processing_times = self.db.query(
                func.avg(VoiceFile.processing_time).label('avg_time'),
                func.min(VoiceFile.processing_time).label('min_time'),
                func.max(VoiceFile.processing_time).label('max_time')
            ).filter(
                VoiceFile.processing_time.isnot(None),
                VoiceFile.status == FileStatus.COMPLETED
            ).first()
            
            # Error rate
            total_processed = self.db.query(VoiceFile).filter(
                VoiceFile.status.in_([FileStatus.COMPLETED, FileStatus.FAILED])
            ).count()
            
            failed_processed = self.db.query(VoiceFile).filter(
                VoiceFile.status == FileStatus.FAILED
            ).count()
            
            error_rate = (failed_processed / total_processed * 100) if total_processed > 0 else 0
            
            # Queue statistics
            pending_files = self.db.query(VoiceFile).filter(
                VoiceFile.status == FileStatus.PENDING
            ).count()
            
            processing_files = self.db.query(VoiceFile).filter(
                VoiceFile.status == FileStatus.ANALYZING
            ).count()
            
            return {
                "processing_times": {
                    "average": float(processing_times.avg_time) if processing_times.avg_time else 0,
                    "minimum": float(processing_times.min_time) if processing_times.min_time else 0,
                    "maximum": float(processing_times.max_time) if processing_times.max_time else 0
                },
                "error_rate": round(error_rate, 2),
                "queue_status": {
                    "pending": pending_files,
                    "processing": processing_files
                },
                "total_processed": total_processed
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": f"Failed to get performance metrics: {str(e)}"}
    
    def _get_file_status_distribution(self) -> Dict[str, int]:
        """Get distribution of file statuses."""
        status_counts = {}
        for status in FileStatus:
            count = self.db.query(VoiceFile).filter(VoiceFile.status == status).count()
            status_counts[status.value] = count
        return status_counts
    
    def _get_recent_activity(self, days: int) -> Dict[str, Any]:
        """Get recent system activity."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Recent uploads
        recent_uploads = self.db.query(VoiceFile).filter(
            VoiceFile.created_at >= cutoff_date
        ).count()
        
        # Recent analyses
        recent_analyses = self.db.query(VoiceAnalysis).filter(
            VoiceAnalysis.created_at >= cutoff_date
        ).count()
        
        # New users
        new_users = self.db.query(User).filter(
            User.created_at >= cutoff_date
        ).count()
        
        return {
            "recent_uploads": recent_uploads,
            "recent_analyses": recent_analyses,
            "new_users": new_users,
            "period_days": days
        }
    
    def _get_processing_statistics(self) -> Dict[str, Any]:
        """Get file processing statistics."""
        completed = self.db.query(VoiceFile).filter(
            VoiceFile.status == FileStatus.COMPLETED
        ).count()
        
        failed = self.db.query(VoiceFile).filter(
            VoiceFile.status == FileStatus.FAILED
        ).count()
        
        processing = self.db.query(VoiceFile).filter(
            VoiceFile.status == FileStatus.ANALYZING
        ).count()
        
        pending = self.db.query(VoiceFile).filter(
            VoiceFile.status == FileStatus.PENDING
        ).count()
        
        total = completed + failed + processing + pending
        success_rate = (completed / (completed + failed) * 100) if (completed + failed) > 0 else 0
        
        return {
            "completed": completed,
            "failed": failed,
            "processing": processing,
            "pending": pending,
            "total": total,
            "success_rate": round(success_rate, 2)
        }
    
    def _get_sentiment_distribution(self) -> Dict[str, int]:
        """Get sentiment analysis distribution."""
        sentiment_counts = {}
        for sentiment in SentimentType:
            count = self.db.query(VoiceAnalysis).filter(
                VoiceAnalysis.sentiment == sentiment
            ).count()
            sentiment_counts[sentiment.value] = count
        return sentiment_counts
    
    def _get_registration_trend(self) -> List[Dict[str, Any]]:
        """Get user registration trend over last 12 months."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=365)
        
        # Group by month
        query = self.db.query(
            func.date_format(User.created_at, '%Y-%m').label('month'),
            func.count(User.id).label('count')
        ).filter(
            User.created_at >= start_date
        ).group_by(
            func.date_format(User.created_at, '%Y-%m')
        ).order_by('month')
        
        results = query.all()
        return [{"month": r.month, "count": r.count} for r in results]
    
    def _get_most_active_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most active users by file upload count."""
        query = self.db.query(
            User.name,
            User.email,
            func.count(VoiceFile.id).label('upload_count')
        ).join(
            VoiceFile, User.id == VoiceFile.uploaded_by
        ).group_by(
            User.id, User.name, User.email
        ).order_by(
            func.count(VoiceFile.id).desc()
        ).limit(limit)
        
        results = query.all()
        return [
            {
                "name": r.name,
                "email": r.email,
                "upload_count": r.upload_count
            }
            for r in results
        ]
    
    def _get_file_size_statistics(self) -> Dict[str, Any]:
        """Get file size statistics."""
        query = self.db.query(
            func.avg(VoiceFile.file_size).label('avg_size'),
            func.min(VoiceFile.file_size).label('min_size'),
            func.max(VoiceFile.file_size).label('max_size'),
            func.sum(VoiceFile.file_size).label('total_size')
        ).filter(VoiceFile.file_size.isnot(None))
        
        result = query.first()
        return {
            "average": float(result.avg_size) if result.avg_size else 0,
            "minimum": float(result.min_size) if result.min_size else 0,
            "maximum": float(result.max_size) if result.max_size else 0,
            "total": float(result.total_size) if result.total_size else 0
        }
    
    def _get_upload_trend(self, days: int) -> List[Dict[str, Any]]:
        """Get file upload trend."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = self.db.query(
            func.date(VoiceFile.created_at).label('date'),
            func.count(VoiceFile.id).label('count')
        ).filter(
            VoiceFile.created_at >= start_date
        ).group_by(
            func.date(VoiceFile.created_at)
        ).order_by('date')
        
        results = query.all()
        return [
            {
                "date": r.date.strftime('%Y-%m-%d'),
                "count": r.count
            }
            for r in results
        ]
    
    def _get_processing_success_rate(self) -> float:
        """Get overall processing success rate."""
        completed = self.db.query(VoiceFile).filter(
            VoiceFile.status == FileStatus.COMPLETED
        ).count()
        
        total_processed = self.db.query(VoiceFile).filter(
            VoiceFile.status.in_([FileStatus.COMPLETED, FileStatus.FAILED])
        ).count()
        
        return (completed / total_processed * 100) if total_processed > 0 else 0
    
    def _get_average_processing_time(self) -> float:
        """Get average processing time in seconds."""
        result = self.db.query(
            func.avg(VoiceFile.processing_time).label('avg_time')
        ).filter(
            VoiceFile.processing_time.isnot(None),
            VoiceFile.status == FileStatus.COMPLETED
        ).first()
        
        return float(result.avg_time) if result.avg_time else 0
    
    def _get_sentiment_trend(self, days: int) -> List[Dict[str, Any]]:
        """Get sentiment analysis trend over time."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = self.db.query(
            func.date(VoiceAnalysis.created_at).label('date'),
            VoiceAnalysis.sentiment,
            func.count(VoiceAnalysis.id).label('count')
        ).filter(
            VoiceAnalysis.created_at >= start_date
        ).group_by(
            func.date(VoiceAnalysis.created_at),
            VoiceAnalysis.sentiment
        ).order_by('date')
        
        results = query.all()
        return [
            {
                "date": r.date.strftime('%Y-%m-%d'),
                "sentiment": r.sentiment.value,
                "count": r.count
            }
            for r in results
        ]
    
    def _get_top_mentioned_products(self, limit: int) -> List[Dict[str, Any]]:
        """Get top mentioned products in analyses."""
        # This requires parsing product_names JSON field
        query = text("""
            SELECT 
                JSON_UNQUOTE(JSON_EXTRACT(product_names, '$[0]')) as product_name,
                COUNT(*) as mention_count
            FROM voice_analyses 
            WHERE product_names IS NOT NULL 
                AND JSON_VALID(product_names) = 1
                AND JSON_LENGTH(product_names) > 0
            GROUP BY JSON_UNQUOTE(JSON_EXTRACT(product_names, '$[0]'))
            ORDER BY mention_count DESC
            LIMIT :limit
        """)
        
        results = self.db.execute(query, {"limit": limit}).fetchall()
        return [
            {
                "product_name": r.product_name,
                "mention_count": r.mention_count
            }
            for r in results if r.product_name
        ]
    
    def _get_top_feedback_categories(self, limit: int) -> List[Dict[str, Any]]:
        """Get top feedback categories."""
        query = self.db.query(
            VoiceAnalysis.feedback_category,
            func.count(VoiceAnalysis.id).label('count')
        ).filter(
            VoiceAnalysis.feedback_category.isnot(None),
            VoiceAnalysis.feedback_category != ''
        ).group_by(
            VoiceAnalysis.feedback_category
        ).order_by(
            func.count(VoiceAnalysis.id).desc()
        ).limit(limit)
        
        results = query.all()
        return [
            {
                "category": r.feedback_category,
                "count": r.count
            }
            for r in results
        ]
    
    def _get_analysis_quality_metrics(self) -> Dict[str, float]:
        """Get analysis quality metrics."""
        # Average confidence score (if available in analysis model)
        # For now, return placeholder metrics
        return {
            "average_confidence": 0.85,
            "high_confidence_rate": 0.72,
            "low_confidence_rate": 0.28
        }
    
    def _get_daily_analysis_volume(self, days: int) -> List[Dict[str, Any]]:
        """Get daily analysis volume."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = self.db.query(
            func.date(VoiceAnalysis.created_at).label('date'),
            func.count(VoiceAnalysis.id).label('count')
        ).filter(
            VoiceAnalysis.created_at >= start_date
        ).group_by(
            func.date(VoiceAnalysis.created_at)
        ).order_by('date')
        
        results = query.all()
        return [
            {
                "date": r.date.strftime('%Y-%m-%d'),
                "count": r.count
            }
            for r in results
        ]
    
    def _empty_dashboard_stats(self) -> Dict[str, Any]:
        """Return empty dashboard statistics."""
        return {
            "overview": {
                "total_users": 0,
                "total_files": 0,
                "total_analyses": 0,
                "total_labels": 0
            },
            "file_status": {},
            "recent_activity": {
                "recent_uploads": 0,
                "recent_analyses": 0,
                "new_users": 0
            },
            "processing_stats": {
                "success_rate": 0
            },
            "sentiment_distribution": {},
            "error": "Failed to load dashboard statistics"
        }