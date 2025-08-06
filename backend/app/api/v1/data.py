"""
Data query and dashboard API endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ...database import get_db
from ...schemas.analysis import AnalysisResponse, AnalysisFilterParams, DashboardData
from ...schemas.common import PaginationParams, PaginatedResponse
from ...repositories.analysis import AnalysisRepository
from ...repositories.file import FileRepository
from ...core.dependencies import get_current_user
from ...models.user import User
from ...models.analysis import SentimentType

router = APIRouter()


@router.get("/analysis", response_model=PaginatedResponse[AnalysisResponse])
async def get_analysis_data(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_names: Optional[List[str]] = Query(None),
    feedback_categories: Optional[List[str]] = Query(None),
    sentiments: Optional[List[SentimentType]] = Query(None),
    uploaders: Optional[List[str]] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """分頁查詢分析結果"""
    analysis_repo = AnalysisRepository(db)
    
    pagination = PaginationParams(page=page, page_size=page_size)
    
    # Get filtered analysis results
    analyses = analysis_repo.get_multi_with_file_info(
        skip=pagination.offset,
        limit=pagination.page_size,
        product_names=product_names,
        feedback_categories=feedback_categories,
        sentiments=sentiments,
        uploaders=uploaders,
        start_date=start_date,
        end_date=end_date
    )
    
    # Get total count
    total = analysis_repo.count_with_filters(
        product_names=product_names,
        feedback_categories=feedback_categories,
        sentiments=sentiments,
        uploaders=uploaders,
        start_date=start_date,
        end_date=end_date
    )
    
    # Convert to response format
    analysis_responses = []
    for analysis in analyses:
        analysis_response = AnalysisResponse.from_orm(analysis)
        if analysis.file:
            analysis_response.filename = analysis.file.original_filename
            analysis_response.upload_time = analysis.file.created_at
            if analysis.file.uploader:
                analysis_response.uploader_name = analysis.file.uploader.name
        analysis_responses.append(analysis_response)
    
    return PaginatedResponse.create(
        items=analysis_responses,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get("/files", response_model=PaginatedResponse)
async def get_files_data(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """分頁查詢文件"""
    file_repo = FileRepository(db)
    
    pagination = PaginationParams(page=page, page_size=page_size)
    
    files = file_repo.get_multi_with_uploader(
        skip=pagination.offset,
        limit=pagination.page_size
    )
    
    total = file_repo.count()
    
    return PaginatedResponse.create(
        items=files,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取儀表盤數據"""
    analysis_repo = AnalysisRepository(db)
    file_repo = FileRepository(db)
    
    # Get basic counts
    total_files = file_repo.count()
    total_analyses = analysis_repo.count()
    
    # Get sentiment distribution for pie chart
    sentiment_dist = analysis_repo.get_sentiment_distribution()
    sentiment_chart = {
        "type": "pie",
        "title": "情緒分布",
        "data": [
            {"name": "正面", "value": sentiment_dist.get("positive", 0)},
            {"name": "中性", "value": sentiment_dist.get("neutral", 0)},
            {"name": "負面", "value": sentiment_dist.get("negative", 0)}
        ]
    }
    
    # Get product distribution with sentiment for stacked bar chart
    product_dist = analysis_repo.get_product_distribution_with_sentiment(limit=10)
    product_chart = {
        "type": "bar",
        "title": "熱門產品討論度 Top10",
        "data": [
            {
                "name": item["product"] if item["product"] is not None else "未分類", 
                "value": item["count"],
                "positive_count": item["positive_count"],
                "neutral_count": item["neutral_count"],
                "negative_count": item["negative_count"]
            }
            for item in product_dist
        ]
    }
    
    # Get category distribution with sentiment for stacked bar chart
    category_dist = analysis_repo.get_category_distribution_with_sentiment(limit=10)
    category_chart = {
        "type": "bar",
        "title": "反饋類別分布",
        "data": [
            {
                "name": item["category"] if item["category"] and item["category"].strip() else "未分類", 
                "value": item["count"],
                "positive_count": item["positive_count"],
                "neutral_count": item["neutral_count"],
                "negative_count": item["negative_count"]
            }
            for item in category_dist
        ]
    }
    
    # Get daily trend for line chart
    daily_trend = analysis_repo.get_daily_trend(days=30)
    trend_chart = {
        "type": "line",
        "title": "分析數量趨勢（近30天）",
        "data": daily_trend
    }
    
    # Feedback trend (same data for now)
    feedback_trend_chart = {
        "type": "line",
        "title": "反饋次數趨勢",
        "data": daily_trend
    }
    
    return DashboardData(
        total_files=total_files,
        total_analyses=total_analyses,
        sentiment_chart=sentiment_chart,
        product_chart=product_chart,
        category_chart=category_chart,
        trend_chart=trend_chart,
        feedback_trend_chart=feedback_trend_chart
    )


@router.get("/export")
async def export_data(
    format: str = Query("excel", regex="^(excel|csv)$"),
    product_names: Optional[List[str]] = Query(None),
    feedback_categories: Optional[List[str]] = Query(None),
    sentiments: Optional[List[SentimentType]] = Query(None),
    uploaders: Optional[List[str]] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """數據導出"""
    from ...core.permissions import PermissionChecker
    
    # Check export permission
    if not PermissionChecker.can_export_data(current_user.role):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to export data"
        )
    
    analysis_repo = AnalysisRepository(db)
    
    # Get filtered data (without pagination for export)
    analyses = analysis_repo.get_multi_with_file_info(
        skip=0,
        limit=10000,  # Large limit for export
        product_names=product_names,
        feedback_categories=feedback_categories,
        sentiments=sentiments,
        uploaders=uploaders,
        start_date=start_date,
        end_date=end_date
    )
    
    # For now, return the data structure
    # In production, you would generate actual Excel/CSV files
    export_data = []
    for analysis in analyses:
        export_data.append({
            "分析ID": analysis.id,
            "文件名": analysis.file.original_filename if analysis.file else "",
            "產品名稱": analysis.product_names,
            "情緒傾向": analysis.sentiment.value,
            "反饋分類": analysis.feedback_category,
            "反饋摘要": analysis.feedback_summary,
            "上傳者": analysis.file.uploader.name if analysis.file and analysis.file.uploader else "",
            "分析時間": analysis.analysis_time.isoformat(),
            "轉錄內容": analysis.transcript[:100] + "..." if analysis.transcript else ""
        })
    
    return {
        "format": format,
        "total_records": len(export_data),
        "export_time": datetime.utcnow().isoformat(),
        "data": export_data,
        "message": f"Data exported successfully in {format} format"
    }


@router.post("/search")
async def advanced_search(
    filter_params: AnalysisFilterParams,
    pagination: PaginationParams,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """高級搜索"""
    analysis_repo = AnalysisRepository(db)
    
    # Get filtered analysis results
    analyses = analysis_repo.get_multi_with_file_info(
        skip=pagination.offset,
        limit=pagination.page_size,
        product_names=filter_params.product_names,
        feedback_categories=filter_params.feedback_categories,
        sentiments=filter_params.sentiments,
        uploaders=filter_params.uploaders,
        start_date=filter_params.start_date,
        end_date=filter_params.end_date
    )
    
    # Get total count
    total = analysis_repo.count_with_filters(
        product_names=filter_params.product_names,
        feedback_categories=filter_params.feedback_categories,
        sentiments=filter_params.sentiments,
        uploaders=filter_params.uploaders,
        start_date=filter_params.start_date,
        end_date=filter_params.end_date
    )
    
    # Convert to response format
    analysis_responses = []
    for analysis in analyses:
        analysis_response = AnalysisResponse.from_orm(analysis)
        if analysis.file:
            analysis_response.filename = analysis.file.original_filename
            analysis_response.upload_time = analysis.file.created_at
            if analysis.file.uploader:
                analysis_response.uploader_name = analysis.file.uploader.name
        analysis_responses.append(analysis_response)
    
    return PaginatedResponse.create(
        items=analysis_responses,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get("/time-series")
async def get_time_series_data(
    product_names: Optional[List[str]] = Query(None),
    sentiments: Optional[List[SentimentType]] = Query(None),
    time_period: str = Query("week", regex="^(week|month|year)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取維度組合的時間序列數據"""
    # 參數驗證
    if not sentiments:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="sentiments is required")
    
    analysis_repo = AnalysisRepository(db)
    
    # 計算時間範圍
    from datetime import timedelta
    end_date = datetime.utcnow()
    if time_period == "week":
        start_date = end_date - timedelta(days=7)
        days = 7
    elif time_period == "month":
        start_date = end_date - timedelta(days=30)
        days = 30
    else:  # year
        start_date = end_date - timedelta(days=365)
        days = 365
    
    # 生成日期標籤
    labels = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        labels.append(date.strftime("%Y-%m-%d"))
    
    # 定義顏色
    colors = [
        '#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', 
        '#ef4444', '#6366f1', '#14b8a6', '#ec4899', 
        '#84cc16', '#f97316'
    ]
    
    # 為每個產品-情緒組合創建數據集
    datasets = []
    color_index = 0
    
    # Handle case when product_names is None or empty - show unclassified data
    products_to_process = product_names if product_names else ['未分類']
    
    for product in products_to_process:
        for sentiment in sentiments:
            # 獲取該組合的每日數據
            # If product is '未分類', pass None to get unclassified records
            product_filter = None if product == '未分類' else product
            daily_counts = analysis_repo.get_daily_counts_by_product_sentiment(
                product_name=product_filter,
                sentiment=sentiment,
                start_date=start_date,
                end_date=end_date
            )
            
            # 將數據映射到日期標籤
            data_map = {item["date"]: item["count"] for item in daily_counts}
            data = [data_map.get(label, 0) for label in labels]
            
            # 將中文情緒轉換
            sentiment_cn = {
                SentimentType.POSITIVE: "正面",
                SentimentType.NEGATIVE: "負面", 
                SentimentType.NEUTRAL: "中性"
            }.get(sentiment, sentiment.value)
            
            datasets.append({
                "label": f"{product} - {sentiment_cn}",
                "data": data,
                "borderColor": colors[color_index % len(colors)],
                "backgroundColor": f"{colors[color_index % len(colors)]}20",
                "borderWidth": 2,
                "tension": 0,
                "pointRadius": 4,
                "pointHoverRadius": 6
            })
            color_index += 1
    
    return {
        "labels": labels,
        "datasets": datasets
    }


