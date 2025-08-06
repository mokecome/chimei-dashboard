"""
Base repository class with common CRUD operations.
"""
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from ..database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get(self, id: Any) -> Optional[ModelType]:
        """Get a record by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None,
        desc_order: bool = False
    ) -> List[ModelType]:
        """Get multiple records with pagination and sorting."""
        query = self.db.query(self.model)
        
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if desc_order:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        """Update an existing record."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field) and value is not None:
                setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: Any) -> Optional[ModelType]:
        """Delete a record by ID."""
        db_obj = self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
        return db_obj
    
    def count(self) -> int:
        """Count total records."""
        return self.db.query(self.model).count()
    
    def exists(self, id: Any) -> bool:
        """Check if a record exists."""
        return self.db.query(self.model).filter(self.model.id == id).first() is not None