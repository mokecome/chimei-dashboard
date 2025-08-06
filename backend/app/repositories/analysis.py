"""
Analysis repository for analysis-related database operations.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, func, or_

from ..models.analysis import VoiceAnalysis, SentimentType
from ..models.file import VoiceFile
from ..models.user import User
from .base import BaseRepository


class AnalysisRepository(BaseRepository[VoiceAnalysis]):
    """Analysis repository with analysis-specific operations."""
    
    def __init__(self, db: Session):
        super().__init__(VoiceAnalysis, db)
    
    def get_with_file_info(self, analysis_id: str) -> Optional[VoiceAnalysis]:
        """Get analysis with file and uploader information."""
        return (
            self.db.query(VoiceAnalysis)
            .options(
                joinedload(VoiceAnalysis.file).joinedload(VoiceFile.uploader)
            )
            .filter(VoiceAnalysis.id == analysis_id)
            .first()
        )
    
    def get_by_file_id(self, file_id: str) -> Optional[VoiceAnalysis]:
        """Get analysis by file ID."""
        return (
            self.db.query(VoiceAnalysis)
            .filter(VoiceAnalysis.file_id == file_id)
            .first()
        )
    
    def get_multi_with_file_info(
        self,
        skip: int = 0,
        limit: int = 100,
        product_names: Optional[List[str]] = None,
        feedback_categories: Optional[List[str]] = None,
        sentiments: Optional[List[SentimentType]] = None,
        uploaders: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[VoiceAnalysis]:
        """Get multiple analyses with file information and filtering."""
        query = (
            self.db.query(VoiceAnalysis)
            .options(
                joinedload(VoiceAnalysis.file).joinedload(VoiceFile.uploader)
            )
            .order_by(desc(VoiceAnalysis.analysis_time))
        )
        
        # Apply filters
        if product_names:
            # Filter by product names in JSON array, also include records with null/empty product_names
            product_conditions = []
            for product in product_names:
                product_conditions.append(
                    VoiceAnalysis.product_names.contains(f'"{product}"')
                )
            # Also include records where product_names is null (no product identified)
            product_conditions.append(
                or_(
                    VoiceAnalysis.product_names.is_(None),
                    VoiceAnalysis.product_names.like('null')
                )
            )
            query = query.filter(or_(*product_conditions))
        
        if feedback_categories:
            query = query.filter(VoiceAnalysis.feedback_category.in_(feedback_categories))
        
        if sentiments:
            query = query.filter(VoiceAnalysis.sentiment.in_(sentiments))
        
        if uploaders:
            query = query.join(VoiceFile).filter(VoiceFile.uploaded_by.in_(uploaders))
        
        if start_date or end_date:
            # Ensure VoiceFile is joined if not already
            if not uploaders:  # If not already joined via uploaders filter
                query = query.join(VoiceFile, VoiceAnalysis.file_id == VoiceFile.id)
        
        if start_date:
            query = query.filter(VoiceFile.created_at >= start_date)
        
        if end_date:
            query = query.filter(VoiceFile.created_at <= end_date)
        
        return query.offset(skip).limit(limit).all()
    
    def count_with_filters(
        self,
        product_names: Optional[List[str]] = None,
        feedback_categories: Optional[List[str]] = None,
        sentiments: Optional[List[SentimentType]] = None,
        uploaders: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Count analyses with filters."""
        query = self.db.query(VoiceAnalysis)
        
        # Apply filters (same as get_multi_with_file_info)
        if product_names:
            product_conditions = []
            for product in product_names:
                product_conditions.append(
                    VoiceAnalysis.product_names.contains(f'"{product}"')
                )
            # Also include records where product_names is null (no product identified)
            product_conditions.append(
                or_(
                    VoiceAnalysis.product_names.is_(None),
                    VoiceAnalysis.product_names.like('null')
                )
            )
            query = query.filter(or_(*product_conditions))
        
        if feedback_categories:
            query = query.filter(VoiceAnalysis.feedback_category.in_(feedback_categories))
        
        if sentiments:
            query = query.filter(VoiceAnalysis.sentiment.in_(sentiments))
        
        if uploaders:
            query = query.join(VoiceFile).filter(VoiceFile.uploaded_by.in_(uploaders))
        
        if start_date or end_date:
            # Ensure VoiceFile is joined if not already
            if not uploaders:  # If not already joined via uploaders filter
                query = query.join(VoiceFile, VoiceAnalysis.file_id == VoiceFile.id)
        
        if start_date:
            query = query.filter(VoiceFile.created_at >= start_date)
        
        if end_date:
            query = query.filter(VoiceFile.created_at <= end_date)
        
        return query.count()
    
    def get_sentiment_distribution(self) -> dict:
        """Get sentiment distribution statistics."""
        result = (
            self.db.query(
                VoiceAnalysis.sentiment,
                func.count(VoiceAnalysis.id).label('count')
            )
            .group_by(VoiceAnalysis.sentiment)
            .all()
        )
        
        return {sentiment.value: count for sentiment, count in result}
    
    def get_product_distribution(self, limit: int = 10) -> List[dict]:
        """Get top products by frequency."""
        # This is simplified - in reality you'd need to parse JSON properly
        result = (
            self.db.query(
                VoiceAnalysis.product_names,
                func.count(VoiceAnalysis.id).label('count')
            )
            .filter(VoiceAnalysis.product_names.isnot(None))
            .group_by(VoiceAnalysis.product_names)
            .order_by(desc('count'))
            .limit(limit)
            .all()
        )
        
        return [{'product': product, 'count': count} for product, count in result]
    
    def get_product_distribution_with_sentiment(self, limit: int = 10) -> List[dict]:
        """Get top products with sentiment distribution."""
        # Get top products first, including None values (represent as "未分類")
        top_products = (
            self.db.query(
                VoiceAnalysis.product_names,
                func.count(VoiceAnalysis.id).label('total_count')
            )
            .group_by(VoiceAnalysis.product_names)
            .order_by(desc('total_count'))
            .limit(limit)
            .all()
        )
        
        result = []
        for product_name, total_count in top_products:
            # Get sentiment distribution for this product
            if product_name is None or product_name == 'null':
                # Handle None/null products separately - they are stored as JSON 'null' in DB
                sentiment_dist = (
                    self.db.query(
                        VoiceAnalysis.sentiment,
                        func.count(VoiceAnalysis.id).label('count')
                    )
                    .filter(func.json_unquote(VoiceAnalysis.product_names) == 'null')
                    .group_by(VoiceAnalysis.sentiment)
                    .all()
                )
            else:
                sentiment_dist = (
                    self.db.query(
                        VoiceAnalysis.sentiment,
                        func.count(VoiceAnalysis.id).label('count')
                    )
                    .filter(VoiceAnalysis.product_names == product_name)
                    .group_by(VoiceAnalysis.sentiment)
                    .all()
                )
            
            # Initialize sentiment counts
            positive_count = 0
            neutral_count = 0
            negative_count = 0
            
            # Fill in actual counts
            for sentiment, count in sentiment_dist:
                if sentiment == SentimentType.POSITIVE:
                    positive_count = count
                elif sentiment == SentimentType.NEUTRAL:
                    neutral_count = count
                elif sentiment == SentimentType.NEGATIVE:
                    negative_count = count
            
            result.append({
                'product': product_name,
                'count': total_count,
                'positive_count': positive_count,
                'neutral_count': neutral_count,
                'negative_count': negative_count
            })
        
        return result
    
    
    def get_category_distribution(self, limit: int = 10) -> List[dict]:
        """Get feedback category distribution."""
        result = (
            self.db.query(
                VoiceAnalysis.feedback_category,
                func.count(VoiceAnalysis.id).label('count')
            )
            .filter(VoiceAnalysis.feedback_category.isnot(None))
            .group_by(VoiceAnalysis.feedback_category)
            .order_by(desc('count'))
            .limit(limit)
            .all()
        )
        
        return [{'category': category, 'count': count} for category, count in result]
    
    def get_category_distribution_with_sentiment(self, limit: int = 10) -> List[dict]:
        """Get feedback categories with sentiment distribution."""
        # Get top categories first, including None/empty values (represent as "未分類")
        top_categories = (
            self.db.query(
                VoiceAnalysis.feedback_category,
                func.count(VoiceAnalysis.id).label('total_count')
            )
            .group_by(VoiceAnalysis.feedback_category)
            .order_by(desc('total_count'))
            .limit(limit)
            .all()
        )
        
        result = []
        for category, total_count in top_categories:
            # Get sentiment distribution for this category
            if category is None or category == '':
                # Handle None/empty categories separately
                sentiment_dist = (
                    self.db.query(
                        VoiceAnalysis.sentiment,
                        func.count(VoiceAnalysis.id).label('count')
                    )
                    .filter(
                        or_(
                            VoiceAnalysis.feedback_category.is_(None),
                            VoiceAnalysis.feedback_category == ''
                        )
                    )
                    .group_by(VoiceAnalysis.sentiment)
                    .all()
                )
            else:
                sentiment_dist = (
                    self.db.query(
                        VoiceAnalysis.sentiment,
                        func.count(VoiceAnalysis.id).label('count')
                    )
                    .filter(VoiceAnalysis.feedback_category == category)
                    .group_by(VoiceAnalysis.sentiment)
                    .all()
                )
            
            # Initialize sentiment counts
            positive_count = 0
            neutral_count = 0
            negative_count = 0
            
            # Fill in actual counts
            for sentiment, count in sentiment_dist:
                if sentiment == SentimentType.POSITIVE:
                    positive_count = count
                elif sentiment == SentimentType.NEUTRAL:
                    neutral_count = count
                elif sentiment == SentimentType.NEGATIVE:
                    negative_count = count
            
            result.append({
                'category': category,
                'count': total_count,
                'positive_count': positive_count,
                'neutral_count': neutral_count,
                'negative_count': negative_count
            })
        
        return result
    
    
    def get_daily_trend(self, days: int = 30) -> List[dict]:
        """Get daily analysis trend based on file upload time."""
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        result = (
            self.db.query(
                func.date(VoiceFile.created_at).label('date'),
                func.count(VoiceAnalysis.id).label('count')
            )
            .join(VoiceFile, VoiceAnalysis.file_id == VoiceFile.id)
            .filter(VoiceFile.created_at >= start_date)
            .group_by(func.date(VoiceFile.created_at))
            .order_by('date')
            .all()
        )
        
        return [{'date': str(date), 'count': count} for date, count in result]
    
    def get_recent_analyses(self, limit: int = 10) -> List[VoiceAnalysis]:
        """Get recent analyses."""
        return (
            self.db.query(VoiceAnalysis)
            .options(
                joinedload(VoiceAnalysis.file).joinedload(VoiceFile.uploader)
            )
            .order_by(desc(VoiceAnalysis.analysis_time))
            .limit(limit)
            .all()
        )
    
    def get_daily_counts_by_product_sentiment(
        self, 
        product_name: Optional[str], 
        sentiment: SentimentType,
        start_date: datetime,
        end_date: datetime
    ) -> List[dict]:
        """Get daily counts for a specific product-sentiment combination based on file upload time."""
        query = (
            self.db.query(
                func.date(VoiceFile.created_at).label('date'),
                func.count(VoiceAnalysis.id).label('count')
            )
            .join(VoiceFile, VoiceAnalysis.file_id == VoiceFile.id)
            .filter(
                VoiceFile.created_at >= start_date,
                VoiceFile.created_at <= end_date,
                VoiceAnalysis.sentiment == sentiment
            )
        )
        
        # Add product filter based on whether product_name is provided
        if product_name is None:
            # Show records with unclassified product_names
            # Based on database inspection, unclassified records have product_names LIKE 'null'
            query = query.filter(VoiceAnalysis.product_names.like('null'))
        else:
            # Show records that contain the specific product name
            # Use simple contains since product_names is stored as JSON string
            query = query.filter(VoiceAnalysis.product_names.contains(product_name))
        
        result = (
            query
            .group_by(func.date(VoiceFile.created_at))
            .order_by('date')
            .all()
        )
        
        return [{'date': str(date), 'count': count} for date, count in result]