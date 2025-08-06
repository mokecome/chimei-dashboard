"""
Label management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...schemas.label import (
    ProductLabelCreate, ProductLabelUpdate, ProductLabelResponse,
    FeedbackCategoryCreate, FeedbackCategoryUpdate, FeedbackCategoryResponse,
    LabelBatchCreate, LabelBatchResponse
)
from ...repositories.label import LabelRepository
from ...core.dependencies import require_permission, get_current_user
from ...models.user import User

router = APIRouter()


# Product Labels
@router.get("/products", response_model=List[ProductLabelResponse])
async def get_product_labels(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取產品標籤列表"""
    label_repo = LabelRepository(db)
    return label_repo.get_product_labels(active_only=active_only, limit=1000)


@router.post("/products", response_model=ProductLabelResponse)
async def create_product_label(
    label_data: ProductLabelCreate,
    current_user: User = Depends(require_permission("write", "labels")),
    db: Session = Depends(get_db)
):
    """創建產品標籤"""
    label_repo = LabelRepository(db)
    
    # Check if label already exists
    existing = label_repo.get_product_label_by_name(label_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product label with this name already exists"
        )
    
    label_dict = label_data.dict()
    label_dict["created_by"] = current_user.id
    
    return label_repo.create_product_label(label_dict)


@router.post("/products/batch", response_model=LabelBatchResponse)
async def create_product_labels_batch(
    batch_data: LabelBatchCreate,
    current_user: User = Depends(require_permission("write", "labels")),
    db: Session = Depends(get_db)
):
    """批量創建產品標籤"""
    label_repo = LabelRepository(db)
    
    successful_labels = []
    failed_labels = []
    
    for label_name in batch_data.labels:
        try:
            # Check if label already exists
            if label_repo.get_product_label_by_name(label_name):
                failed_labels.append({
                    "name": label_name,
                    "reason": "Label already exists"
                })
                continue
            
            label_dict = {
                "name": label_name,
                "is_active": True,
                "created_by": current_user.id
            }
            
            label_repo.create_product_label(label_dict)
            successful_labels.append(label_name)
            
        except Exception as e:
            failed_labels.append({
                "name": label_name,
                "reason": str(e)
            })
    
    return LabelBatchResponse(
        successful_labels=successful_labels,
        failed_labels=failed_labels,
        total_labels=len(batch_data.labels),
        successful_count=len(successful_labels),
        failed_count=len(failed_labels)
    )


# Feedback Categories
@router.get("/categories", response_model=List[FeedbackCategoryResponse])
async def get_feedback_categories(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取反饋分類列表"""
    label_repo = LabelRepository(db)
    return label_repo.get_feedback_categories(active_only=active_only, limit=1000)


@router.post("/categories", response_model=FeedbackCategoryResponse)
async def create_feedback_category(
    category_data: FeedbackCategoryCreate,
    current_user: User = Depends(require_permission("write", "labels")),
    db: Session = Depends(get_db)
):
    """創建反饋分類"""
    label_repo = LabelRepository(db)
    
    # Check if category already exists
    existing = label_repo.get_feedback_category_by_name(category_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback category with this name already exists"
        )
    
    category_dict = category_data.dict()
    category_dict["created_by"] = current_user.id
    
    return label_repo.create_feedback_category(category_dict)


@router.put("/categories/{category_id}", response_model=FeedbackCategoryResponse)
async def update_feedback_category(
    category_id: int,
    category_data: FeedbackCategoryUpdate,
    current_user: User = Depends(require_permission("write", "labels")),
    db: Session = Depends(get_db)
):
    """更新反饋分類"""
    label_repo = LabelRepository(db)
    
    # Check if new name conflicts with existing category
    if category_data.name:
        existing = label_repo.get_feedback_category_by_name(category_data.name)
        if existing and existing.id != category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Feedback category with this name already exists"
            )
    
    category = label_repo.update_feedback_category(category_id, category_data.dict(exclude_unset=True))
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback category not found"
        )
    
    return category


@router.delete("/products/batch")
async def delete_product_labels_batch(
    request: Request,
    current_user: User = Depends(require_permission("write", "labels")),
    db: Session = Depends(get_db)
):
    """批量刪除產品標籤"""
    label_repo = LabelRepository(db)
    
    # 獲取請求體中的產品ID列表
    try:
        body = await request.json()
        print(f"DEBUG: Received body: {body}")
        print(f"DEBUG: Body type: {type(body)}")
        # Handle both direct array and { data: array } formats
        product_ids = body if isinstance(body, list) else body.get('data', [])
        print(f"DEBUG: Extracted product_ids: {product_ids}")
    except Exception as e:
        print(f"DEBUG: Error parsing body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request body: {str(e)}"
        )
    
    deleted_count = 0
    failed_deletions = []
    
    for product_id in product_ids:
        try:
            label = label_repo.delete_product_label(product_id)
            if label:
                deleted_count += 1
            else:
                failed_deletions.append({
                    "id": product_id,
                    "reason": "Product label not found"
                })
        except Exception as e:
            failed_deletions.append({
                "id": product_id,
                "reason": str(e)
            })
    
    return {
        "message": f"Batch deletion completed",
        "deleted_count": deleted_count,
        "failed_count": len(failed_deletions),
        "failed_deletions": failed_deletions
    }


@router.put("/products/{label_id}", response_model=ProductLabelResponse)
async def update_product_label(
    label_id: int,
    label_data: ProductLabelUpdate,
    current_user: User = Depends(require_permission("write", "labels")),
    db: Session = Depends(get_db)
):
    """更新產品標籤"""
    label_repo = LabelRepository(db)
    
    # Check if new name conflicts with existing label
    if label_data.name:
        existing = label_repo.get_product_label_by_name(label_data.name)
        if existing and existing.id != label_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product label with this name already exists"
            )
    
    label = label_repo.update_product_label(label_id, label_data.dict(exclude_unset=True))
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product label not found"
        )
    
    return label


@router.delete("/products/{label_id}")
async def delete_product_label(
    label_id: int,
    current_user: User = Depends(require_permission("write", "labels")),
    db: Session = Depends(get_db)
):
    """刪除產品標籤"""
    label_repo = LabelRepository(db)
    
    label = label_repo.delete_product_label(label_id)
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product label not found"
        )
    
    return {"message": "Product label deleted successfully"}


@router.delete("/categories/batch")
async def delete_feedback_categories_batch(
    request: Request,
    current_user: User = Depends(require_permission("write", "labels")),
    db: Session = Depends(get_db)
):
    """批量刪除反饋分類"""
    label_repo = LabelRepository(db)
    
    # 獲取請求體中的分類ID列表
    try:
        body = await request.json()
        print(f"DEBUG: Received body: {body}")
        print(f"DEBUG: Body type: {type(body)}")
        # Handle both direct array and { data: array } formats
        category_ids = body if isinstance(body, list) else body.get('data', [])
        print(f"DEBUG: Extracted category_ids: {category_ids}")
    except Exception as e:
        print(f"DEBUG: Error parsing body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request body: {str(e)}"
        )
    
    deleted_count = 0
    failed_deletions = []
    
    for category_id in category_ids:
        try:
            category = label_repo.delete_feedback_category(category_id)
            if category:
                deleted_count += 1
            else:
                failed_deletions.append({
                    "id": category_id,
                    "reason": "Feedback category not found"
                })
        except Exception as e:
            failed_deletions.append({
                "id": category_id,
                "reason": str(e)
            })
    
    return {
        "message": f"Batch deletion completed",
        "deleted_count": deleted_count,
        "failed_count": len(failed_deletions),
        "failed_deletions": failed_deletions
    }


@router.put("/categories/{category_id}", response_model=FeedbackCategoryResponse)
async def update_feedback_category(
    category_id: int,
    category_data: FeedbackCategoryUpdate,
    current_user: User = Depends(require_permission("write", "labels")),
    db: Session = Depends(get_db)
):
    """更新反饋分類"""
    label_repo = LabelRepository(db)
    
    # Check if new name conflicts with existing category
    if category_data.name:
        existing = label_repo.get_feedback_category_by_name(category_data.name)
        if existing and existing.id != category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Feedback category with this name already exists"
            )
    
    category = label_repo.update_feedback_category(category_id, category_data.dict(exclude_unset=True))
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback category not found"
        )
    
    return category


@router.delete("/categories/{category_id}")
async def delete_feedback_category(
    category_id: int,
    current_user: User = Depends(require_permission("write", "labels")),
    db: Session = Depends(get_db)
):
    """刪除反饋分類"""
    label_repo = LabelRepository(db)
    
    category = label_repo.delete_feedback_category(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback category not found"
        )
    
    return {"message": "Feedback category deleted successfully"}