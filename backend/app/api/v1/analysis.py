"""
AI Analysis API endpoints.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...schemas.analysis import AnalysisResponse, AnalysisUpdate
from ...repositories.file import FileRepository
from ...repositories.analysis import AnalysisRepository
from ...repositories.label import LabelRepository
from ...core.dependencies import require_permission, get_current_user
from ...models.user import User
from ...models.file import FileStatus
from ...models.analysis import SentimentType
from ...ai.speech_to_text import speech_service
from ...ai.llm_analyzer import analyze_feedback
import json

router = APIRouter()


def process_file_analysis(file_id: str, db: Session):
    """Background task to process file analysis."""
    file_repo = FileRepository(db)
    analysis_repo = AnalysisRepository(db)
    label_repo = LabelRepository(db)
    
    try:
        # Get file
        file_obj = file_repo.get(file_id)
        if not file_obj:
            return
        
        # Update status to analyzing
        file_repo.update_status(file_id, FileStatus.ANALYZING)
        
        # Get transcript based on file type
        if file_obj.file_format in ['wav', 'mp3']:
            # Convert speech to text for audio files with timeout handling
            try:
                print(f"Starting speech-to-text for file {file_obj.original_filename} (size: {os.path.getsize(file_obj.file_path) / 1024 / 1024:.1f}MB)")
                transcript = speech_service.speech_to_text(file_obj.file_path)
                if not transcript:
                    print(f"Speech-to-text returned empty result for {file_obj.file_path}")
                    file_repo.update_status(file_id, FileStatus.FAILED)
                    return
                print(f"Speech-to-text completed: {len(transcript)} characters")
            except Exception as e:
                print(f"Speech-to-text failed for {file_obj.file_path}: {e}")
                file_repo.update_status(file_id, FileStatus.FAILED)
                return
        elif file_obj.file_format == 'txt':
            # Read text file directly
            try:
                with open(file_obj.file_path, 'r', encoding='utf-8') as f:
                    transcript = f.read().strip()
            except Exception as e:
                print(f"Failed to read text file {file_obj.file_path}: {e}")
                file_repo.update_status(file_id, FileStatus.FAILED)
                return
        else:
            print(f"Unsupported file format: {file_obj.file_format}")
            file_repo.update_status(file_id, FileStatus.FAILED)
            return
        
        if not transcript:
            file_repo.update_status(file_id, FileStatus.FAILED)
            return
        
        # Get product labels and feedback categories for analysis
        product_labels = label_repo.get_product_labels(active_only=True, limit=1000)
        feedback_categories = label_repo.get_feedback_categories(active_only=True, limit=1000)
        
        product_list = "\n".join([label.name for label in product_labels])
        feedback_list = "\n".join([category.name for category in feedback_categories])
        
        # Analyze content with LLM
        analysis_result = analyze_feedback(transcript, product_list, feedback_list)
        
        if "error" in analysis_result:
            file_repo.update_status(file_id, FileStatus.FAILED)
            return
        
        # Parse product names (handle multiple products)
        product_names = []
        if analysis_result.get("product_name"):
            # Split by common delimiters
            products = analysis_result["product_name"].replace("、", ",").replace("，", ",").split(",")
            product_names = [p.strip() for p in products if p.strip() and p.strip() != "無"]
        
        # Create analysis record
        # Map lowercase AI results to uppercase enum values
        sentiment_mapping = {
            "positive": SentimentType.POSITIVE,
            "negative": SentimentType.NEGATIVE,
            "neutral": SentimentType.NEUTRAL
        }
        ai_sentiment = analysis_result.get("evaluation_tendency", "neutral").lower()
        sentiment = sentiment_mapping.get(ai_sentiment, SentimentType.NEUTRAL)
        
        analysis_data = {
            "file_id": file_id,
            "transcript": transcript,
            "sentiment": sentiment,
            "feedback_category": analysis_result.get("feedback_category", ""),
            "feedback_summary": analysis_result.get("feedback_summary", ""),
            "product_names": json.dumps(product_names, ensure_ascii=False) if product_names else None
        }
        
        analysis_repo.create(analysis_data)
        
        # Update file status to completed
        file_repo.update_status(file_id, FileStatus.COMPLETED)
        
    except Exception as e:
        # Update status to failed
        file_repo.update_status(file_id, FileStatus.FAILED)
        print(f"Analysis failed for file {file_id}: {e}")


@router.post("/start/{file_id}")
async def start_analysis(
    file_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("write", "analysis")),
    db: Session = Depends(get_db)
):
    """啟動文件分析"""
    file_repo = FileRepository(db)
    analysis_repo = AnalysisRepository(db)
    
    # Check if file exists
    file_obj = file_repo.get(file_id)
    if not file_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check if analysis already exists
    existing_analysis = analysis_repo.get_by_file_id(file_id)
    if existing_analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis already exists for this file"
        )
    
    # Start background analysis
    background_tasks.add_task(process_file_analysis, file_id, db)
    
    return {"message": "Analysis started", "file_id": file_id}


@router.get("/status/{file_id}")
async def get_analysis_status(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取分析狀態"""
    file_repo = FileRepository(db)
    analysis_repo = AnalysisRepository(db)
    
    # Get file
    file_obj = file_repo.get(file_id)
    if not file_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Get analysis
    analysis = analysis_repo.get_by_file_id(file_id)
    
    return {
        "file_id": file_id,
        "file_status": file_obj.status,
        "analysis_exists": analysis is not None,
        "analysis_id": analysis.id if analysis else None
    }


@router.get("/result/{file_id}", response_model=AnalysisResponse)
async def get_analysis_result(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取分析結果"""
    analysis_repo = AnalysisRepository(db)
    
    # Get analysis with file info
    analysis = analysis_repo.get_by_file_id(file_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    # Convert to response format
    analysis_response = AnalysisResponse.from_orm(analysis)
    if analysis.file:
        analysis_response.filename = analysis.file.original_filename
        analysis_response.upload_time = analysis.file.created_at
        if analysis.file.uploader:
            analysis_response.uploader_name = analysis.file.uploader.name
    
    return analysis_response


@router.post("/batch")
async def batch_analysis(
    file_ids: List[str],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("write", "analysis")),
    db: Session = Depends(get_db)
):
    """批量分析文件"""
    file_repo = FileRepository(db)
    analysis_repo = AnalysisRepository(db)
    
    valid_files = []
    invalid_files = []
    
    for file_id in file_ids:
        # Check if file exists
        file_obj = file_repo.get(file_id)
        if not file_obj:
            invalid_files.append({"file_id": file_id, "reason": "File not found"})
            continue
        
        # Check if analysis already exists
        existing_analysis = analysis_repo.get_by_file_id(file_id)
        if existing_analysis:
            invalid_files.append({"file_id": file_id, "reason": "Analysis already exists"})
            continue
        
        valid_files.append(file_id)
        # Start background analysis
        background_tasks.add_task(process_file_analysis, file_id, db)
    
    return {
        "message": f"Batch analysis started for {len(valid_files)} files",
        "valid_files": valid_files,
        "invalid_files": invalid_files,
        "total_requested": len(file_ids),
        "valid_count": len(valid_files),
        "invalid_count": len(invalid_files)
    }


@router.put("/{file_id}/transcript")
async def update_transcript(
    file_id: str,
    update_data: AnalysisUpdate,
    current_user: User = Depends(require_permission("write", "analysis")),
    db: Session = Depends(get_db)
):
    """更新分析結果的逐字稿內容"""
    analysis_repo = AnalysisRepository(db)
    
    # Get analysis by file ID
    analysis = analysis_repo.get_by_file_id(file_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found for this file"
        )
    
    # Update transcript if provided
    update_dict = {}
    if update_data.transcript is not None:
        update_dict["transcript"] = update_data.transcript
    
    # Update the analysis record
    updated_analysis = analysis_repo.update(analysis, update_dict)
    
    return {
        "message": "Transcript updated successfully",
        "file_id": file_id,
        "analysis_id": updated_analysis.id
    }


@router.get("/statistics/summary")
async def get_analysis_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取分析統計"""
    analysis_repo = AnalysisRepository(db)
    
    return {
        "total_analyses": analysis_repo.count(),
        "sentiment_distribution": analysis_repo.get_sentiment_distribution(),
        "top_products": analysis_repo.get_product_distribution(limit=10),
        "top_categories": analysis_repo.get_category_distribution(limit=10),
        "daily_trend": analysis_repo.get_daily_trend(days=30),
        "recent_analyses": [
            AnalysisResponse.from_orm(analysis) 
            for analysis in analysis_repo.get_recent_analyses(limit=5)
        ]
    }