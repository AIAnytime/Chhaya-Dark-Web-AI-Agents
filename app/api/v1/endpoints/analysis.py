from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from app.models.schemas import AnalysisRequest, AnalysisResponse, AIAnalysis
from app.services.ai_service import ai_service
from app.services.crawler_service import crawler_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start AI analysis of crawled pages"""
    try:
        # Get crawl job
        job = crawler_service.get_job_status(request.crawl_id)
        if not job:
            raise HTTPException(status_code=404, detail="Crawl job not found")
        
        if not job.pages:
            raise HTTPException(status_code=400, detail="No pages found for analysis")
        
        # Prepare pages for analysis
        pages_data = [
            {"url": page.url, "text_content": page.text_content}
            for page in job.pages
        ]
        
        # Start analysis
        analyses = await ai_service.batch_analyze_pages(pages_data)
        
        # Save report
        report_path = await ai_service.save_analysis_report(analyses, request.crawl_id)
        
        # Generate summary stats
        summary_stats = await ai_service.generate_summary_report(analyses)
        
        return AnalysisResponse(
            job_id=f"analysis_{request.crawl_id}",
            crawl_id=request.crawl_id,
            status="completed",
            analyses=analyses,
            summary_stats=summary_stats
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze/{crawl_id}")
async def get_analysis_results(crawl_id: str):
    """Get analysis results for a crawl job"""
    # This would typically fetch from database
    # For now, return placeholder
    return {"message": f"Analysis results for crawl {crawl_id} - implement database storage"}

@router.post("/analyze/single")
async def analyze_single_page(url: str, text_content: str):
    """Analyze a single page"""
    try:
        analysis = await ai_service.analyze_page(url, text_content)
        if not analysis:
            raise HTTPException(status_code=500, detail="Analysis failed")
        
        return analysis
    except Exception as e:
        logger.error(f"Single page analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
