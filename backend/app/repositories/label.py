"""
Label repository for label-related database operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from ..models.label import ProductLabel, FeedbackCategory
from .base import BaseRepository


class LabelRepository:
    """Label repository for both product labels and feedback categories."""
    
    def __init__(self, db: Session):
        self.db = db
        self.product_labels = BaseRepository(ProductLabel, db)
        self.feedback_categories = BaseRepository(FeedbackCategory, db)
    
    # Product Label methods
    def get_product_label(self, label_id: int) -> Optional[ProductLabel]:
        """Get product label by ID."""
        return self.product_labels.get(label_id)
    
    def get_product_labels(
        self, 
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[ProductLabel]:
        """Get product labels with optional filtering."""
        query = (
            self.db.query(ProductLabel)
            .options(joinedload(ProductLabel.creator))
        )
        
        if active_only:
            query = query.filter(ProductLabel.is_active == True)
        
        return query.offset(skip).limit(limit).all()
    
    def create_product_label(self, label_data: dict) -> ProductLabel:
        """Create a new product label."""
        return self.product_labels.create(label_data)
    
    def update_product_label(self, label_id: int, label_data: dict) -> Optional[ProductLabel]:
        """Update a product label."""
        label = self.get_product_label(label_id)
        if label:
            return self.product_labels.update(label, label_data)
        return None
    
    def delete_product_label(self, label_id: int) -> Optional[ProductLabel]:
        """Delete a product label."""
        return self.product_labels.delete(label_id)
    
    def get_product_label_by_name(self, name: str) -> Optional[ProductLabel]:
        """Get product label by name."""
        return (
            self.db.query(ProductLabel)
            .filter(ProductLabel.name == name)
            .first()
        )
    
    def search_product_labels(self, query: str, active_only: bool = True) -> List[ProductLabel]:
        """Search product labels by name."""
        db_query = (
            self.db.query(ProductLabel)
            .filter(ProductLabel.name.contains(query))
        )
        
        if active_only:
            db_query = db_query.filter(ProductLabel.is_active == True)
        
        return db_query.all()
    
    def count_product_labels(self, active_only: bool = True) -> int:
        """Count product labels."""
        query = self.db.query(ProductLabel)
        if active_only:
            query = query.filter(ProductLabel.is_active == True)
        return query.count()
    
    # Feedback Category methods
    def get_feedback_category(self, category_id: int) -> Optional[FeedbackCategory]:
        """Get feedback category by ID."""
        return self.feedback_categories.get(category_id)
    
    def get_feedback_categories(
        self, 
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[FeedbackCategory]:
        """Get feedback categories with optional filtering."""
        query = (
            self.db.query(FeedbackCategory)
            .options(joinedload(FeedbackCategory.creator))
        )
        
        if active_only:
            query = query.filter(FeedbackCategory.is_active == True)
        
        return query.offset(skip).limit(limit).all()
    
    def create_feedback_category(self, category_data: dict) -> FeedbackCategory:
        """Create a new feedback category."""
        return self.feedback_categories.create(category_data)
    
    def update_feedback_category(self, category_id: int, category_data: dict) -> Optional[FeedbackCategory]:
        """Update a feedback category."""
        category = self.get_feedback_category(category_id)
        if category:
            return self.feedback_categories.update(category, category_data)
        return None
    
    def delete_feedback_category(self, category_id: int) -> Optional[FeedbackCategory]:
        """Delete a feedback category."""
        return self.feedback_categories.delete(category_id)
    
    def get_feedback_category_by_name(self, name: str) -> Optional[FeedbackCategory]:
        """Get feedback category by name."""
        return (
            self.db.query(FeedbackCategory)
            .filter(FeedbackCategory.name == name)
            .first()
        )
    
    def search_feedback_categories(self, query: str, active_only: bool = True) -> List[FeedbackCategory]:
        """Search feedback categories by name."""
        db_query = (
            self.db.query(FeedbackCategory)
            .filter(FeedbackCategory.name.contains(query))
        )
        
        if active_only:
            db_query = db_query.filter(FeedbackCategory.is_active == True)
        
        return db_query.all()
    
    def count_feedback_categories(self, active_only: bool = True) -> int:
        """Count feedback categories."""
        query = self.db.query(FeedbackCategory)
        if active_only:
            query = query.filter(FeedbackCategory.is_active == True)
        return query.count()
    
    # Batch operations
    def create_product_labels_batch(self, labels: List[str], created_by: str) -> List[ProductLabel]:
        """Create multiple product labels."""
        created_labels = []
        for label_name in labels:
            # Check if label already exists
            if not self.get_product_label_by_name(label_name):
                label_data = {
                    "name": label_name,
                    "created_by": created_by,
                    "is_active": True
                }
                created_label = self.create_product_label(label_data)
                created_labels.append(created_label)
        
        return created_labels
    
    def create_feedback_categories_batch(self, categories: List[str], created_by: str) -> List[FeedbackCategory]:
        """Create multiple feedback categories."""
        created_categories = []
        for category_name in categories:
            # Check if category already exists
            if not self.get_feedback_category_by_name(category_name):
                category_data = {
                    "name": category_name,
                    "created_by": created_by,
                    "is_active": True
                }
                created_category = self.create_feedback_category(category_data)
                created_categories.append(created_category)
        
        return created_categories