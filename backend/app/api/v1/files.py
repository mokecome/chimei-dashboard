"""
File management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import shutil

from ...database import get_db
from ...schemas.file import FileResponse, FileUploadResponse, FileBatchUploadResponse, FileAnalysisResult
from ...schemas.common import PaginationParams, PaginatedResponse
from ...repositories.file import FileRepository
from ...repositories.analysis import AnalysisRepository
from ...core.dependencies import require_permission, get_current_user
from ...models.user import User
from ...models.file import FileStatus, FileFormat
from ...config import settings
from ...services.analysis_service import AnalysisService
from ...database import SessionLocal
import json
import logging

logger = logging.getLogger(__name__)


def process_file_in_background(file_id: str, db_url: str):
    """Background task to process file analysis."""
    # Create new database session for background task
    db = SessionLocal()
    try:
        analysis_service = AnalysisService(db)
        analysis_result = analysis_service.process_file_analysis(file_id)
        
        if "error" in analysis_result:
            logger.error(f"Background analysis failed for file {file_id}: {analysis_result['error']}")
        else:
            logger.info(f"Background analysis completed for file {file_id}")
    except Exception as e:
        logger.error(f"Background analysis exception for file {file_id}: {str(e)}")
    finally:
        db.close()

router = APIRouter()


def save_uploaded_file(file: UploadFile, user_id: str) -> dict:
    """Save uploaded file and return file info."""
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext[1:] not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions_list)}"
        )
    
    # Generate unique file ID and path
    file_id = str(uuid.uuid4())
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{file_id}{file_ext}")
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Validate file size
    if file_size > settings.MAX_FILE_SIZE:
        os.remove(file_path)  # Clean up
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    return {
        "id": file_id,
        "filename": f"{file_id}{file_ext}",
        "original_filename": file.filename,
        "file_path": file_path,
        "file_size": file_size,
        "file_format": FileFormat(file_ext[1:]),
        "uploaded_by": user_id
    }


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("write", "files")),
    db: Session = Depends(get_db)
):
    """上傳單個文件並啟動自動分析"""
    file_repo = FileRepository(db)
    
    # Save file
    file_info = save_uploaded_file(file, current_user.id)
    
    # Create file record with PENDING status (待分析)
    file_record = file_repo.create(file_info)
    
    # Auto-start analysis for audio and text files (background task)
    if file_record.file_format in [FileFormat.WAV, FileFormat.MP3, FileFormat.TXT]:
        # Use background task to avoid request timeout
        background_tasks.add_task(
            process_file_in_background,
            file_record.id,
            str(db.bind.url)  # Pass database URL for new connection
        )
    
    return FileUploadResponse(
        file_id=file_record.id,
        filename=file_record.original_filename,
        message="File uploaded successfully, analysis started"
    )


@router.post("/batch-upload", response_model=FileBatchUploadResponse)
async def batch_upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_permission("write", "files")),
    db: Session = Depends(get_db)
):
    """批量上傳文件並啟動自動分析"""
    file_repo = FileRepository(db)
    
    successful_uploads = []
    failed_uploads = []
    
    for file in files:
        try:
            # Save file
            file_info = save_uploaded_file(file, current_user.id)
            
            # Create file record with PENDING status (待分析)
            file_record = file_repo.create(file_info)
            
            # Auto-start analysis for audio and text files (background task)
            if file_record.file_format in [FileFormat.WAV, FileFormat.MP3, FileFormat.TXT]:
                # Use background task to avoid request timeout
                background_tasks.add_task(
                    process_file_in_background,
                    file_record.id,
                    str(db.bind.url)  # Pass database URL for new connection
                )
            
            successful_uploads.append(FileUploadResponse(
                file_id=file_record.id,
                filename=file_record.original_filename,
                message="Uploaded successfully, analysis started"
            ))
            
        except Exception as e:
            failed_uploads.append({
                "filename": file.filename,
                "reason": str(e)
            })
    
    return FileBatchUploadResponse(
        successful_uploads=successful_uploads,
        failed_uploads=failed_uploads,
        total_files=len(files),
        successful_count=len(successful_uploads),
        failed_count=len(failed_uploads)
    )


@router.get("/", response_model=PaginatedResponse[FileResponse])
async def get_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[FileStatus] = Query(None),
    format: Optional[FileFormat] = Query(None),
    uploaded_by: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取文件列表"""
    file_repo = FileRepository(db)
    
    pagination = PaginationParams(page=page, page_size=page_size)
    
    files = file_repo.get_multi_with_uploader(
        skip=pagination.offset,
        limit=pagination.page_size,
        status=status,
        format=format,
        uploaded_by=uploaded_by
    )
    
    total = file_repo.count_with_filters(
        status=status,
        format=format,
        uploaded_by=uploaded_by
    )
    
    # Convert to response format with analysis results
    analysis_repo = AnalysisRepository(db)
    file_responses = []
    for file_obj in files:
        file_response = FileResponse.from_orm(file_obj)
        if file_obj.uploader:
            file_response.uploader_name = file_obj.uploader.name
        
        # Get analysis result if exists
        if file_obj.status == FileStatus.COMPLETED:
            analysis = analysis_repo.get_by_file_id(file_obj.id)
            if analysis:
                file_response.analysis_result = FileAnalysisResult(
                    sentiment=analysis.sentiment,
                    feedback_category=analysis.feedback_category,
                    feedback_summary=analysis.feedback_summary,
                    product_names=json.loads(analysis.product_names) if analysis.product_names else [],
                    transcript=analysis.transcript
                )
        
        file_responses.append(file_response)
    
    return PaginatedResponse.create(
        items=file_responses,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取文件詳情"""
    file_repo = FileRepository(db)
    analysis_repo = AnalysisRepository(db)
    
    file_obj = file_repo.get_with_uploader(file_id)
    if not file_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    file_response = FileResponse.from_orm(file_obj)
    if file_obj.uploader:
        file_response.uploader_name = file_obj.uploader.name
    
    # Get analysis result if exists
    if file_obj.status == FileStatus.COMPLETED:
        analysis = analysis_repo.get_by_file_id(file_obj.id)
        if analysis:
            file_response.analysis_result = FileAnalysisResult(
                sentiment=analysis.sentiment,
                feedback_category=analysis.feedback_category,
                feedback_summary=analysis.feedback_summary,
                product_names=json.loads(analysis.product_names) if analysis.product_names else [],
                transcript=analysis.transcript
            )
    
    return file_response


@router.delete("/batch")
async def batch_delete_files(
    request: Request,
    current_user: User = Depends(require_permission("delete", "files")),
    db: Session = Depends(get_db)
):
    """批量刪除文件"""
    file_repo = FileRepository(db)
    
    # 獲取請求體中的文件ID列表
    try:
        body = await request.json()
        # Handle both direct array and { ids: array } formats
        file_ids = body if isinstance(body, list) else body.get('ids', [])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body format"
        )
    
    if not file_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file IDs provided"
        )
    
    successful_deletes = []
    failed_deletes = []
    
    for file_id in file_ids:
        try:
            file_obj = file_repo.get(file_id)
            if not file_obj:
                failed_deletes.append({
                    "id": file_id,
                    "reason": "File not found"
                })
                continue
            
            # Delete physical file
            try:
                if os.path.exists(file_obj.file_path):
                    os.remove(file_obj.file_path)
            except Exception as e:
                # Log error but continue with database deletion
                logger.warning(f"Failed to delete physical file {file_obj.file_path}: {str(e)}")
            
            # Delete from database
            file_repo.delete(file_id)
            successful_deletes.append(file_id)
            
        except Exception as e:
            failed_deletes.append({
                "id": file_id,
                "reason": str(e)
            })
    
    return {
        "message": f"Batch delete completed. Success: {len(successful_deletes)}, Failed: {len(failed_deletes)}",
        "successful_deletes": successful_deletes,
        "failed_deletes": failed_deletes,
        "total_files": len(file_ids),
        "successful_count": len(successful_deletes),
        "failed_count": len(failed_deletes)
    }


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(require_permission("delete", "files")),
    db: Session = Depends(get_db)
):
    """刪除文件"""
    file_repo = FileRepository(db)
    
    file_obj = file_repo.get(file_id)
    if not file_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Delete physical file
    try:
        if os.path.exists(file_obj.file_path):
            os.remove(file_obj.file_path)
    except Exception as e:
        # Log error but continue with database deletion
        pass
    
    # Delete from database
    file_repo.delete(file_id)
    
    return {"message": "File deleted successfully"}




def run_file_analysis(file_id: str, db: Session):
    """Run analysis for a file in background."""
    try:
        analysis_service = AnalysisService(db)
        result = analysis_service.process_file_analysis(file_id)
        
        if "error" in result:
            print(f"Analysis failed for file {file_id}: {result['error']}")
        else:
            print(f"Analysis completed for file {file_id}")
    except Exception as e:
        print(f"Error running analysis for file {file_id}: {e}")
    finally:
        # Ensure database session is closed
        db.close()


@router.post("/{file_id}/reprocess")
async def reprocess_file(
    file_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("write", "files")),
    db: Session = Depends(get_db)
):
    """重新處理文件分析"""
    file_repo = FileRepository(db)
    
    # Check if file exists
    file_obj = file_repo.get(file_id)
    if not file_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check if file is supported format
    if file_obj.file_format not in [FileFormat.WAV, FileFormat.MP3, FileFormat.TXT]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only audio and text files can be reprocessed"
        )
    
    # Reset file status to PENDING before reprocessing
    file_repo.update_status(file_id, FileStatus.PENDING)
    logger.info(f"File {file_id} status reset to PENDING for reprocessing")
    
    # Use background task for reprocessing to avoid timeout and allow status tracking
    background_tasks.add_task(
        process_file_in_background,
        file_id,
        str(db.bind.url)  # Pass database URL for new connection
    )
    
    return {"message": "File reprocessing started", "status": "pending"}


@router.put("/{file_id}/status")
async def update_file_status(
    file_id: str,
    status: FileStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新文件狀態"""
    file_repo = FileRepository(db)
    
    file_obj = file_repo.update_status(file_id, status)
    if not file_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return {"message": f"File status updated to {status.value}"}