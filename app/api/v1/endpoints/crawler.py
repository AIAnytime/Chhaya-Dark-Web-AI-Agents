from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from app.models.schemas import CrawlRequest, CrawlResponse, CrawlJob, TorStatus
from app.services.crawler_service import crawler_service
from app.core.tor_manager import tor_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/tor/status", response_model=TorStatus)
async def check_tor_status():
    """Check Tor connection status"""
    return tor_manager.test_connection()

@router.post("/tor/reset")
async def reset_tor_connection():
    """Reset Tor connection"""
    tor_manager.reset_session()
    return {"message": "Tor connection reset successfully"}

@router.post("/crawl", response_model=CrawlResponse)
async def start_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """Start a new dark web crawl job"""
    try:
        job_id = await crawler_service.start_crawl(
            query=request.query,
            limit=request.limit
        )
        
        return CrawlResponse(
            job_id=job_id,
            status="pending",
            message=f"Crawl job started for query: {request.query}"
        )
    except Exception as e:
        logger.error(f"Failed to start crawl: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/crawl/{job_id}")
async def get_crawl_status(job_id: str):
    """Get status of a crawl job"""
    job = crawler_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    
    # Add AI analysis results if available
    analysis_results = await get_analysis_results_for_job(job_id)
    job_dict = job.dict() if hasattr(job, 'dict') else job.__dict__
    job_dict['analysis_results'] = analysis_results
    
    return job_dict

async def get_analysis_results_for_job(job_id: str):
    """Get AI analysis results for a job"""
    import os
    import json
    from app.core.config import settings
    
    try:
        # Look for analysis report files for this job
        reports_dir = settings.REPORTS_DIR
        analysis_files = []
        
        if os.path.exists(reports_dir):
            for filename in os.listdir(reports_dir):
                if filename.startswith(f"analysis_report_{job_id}") and filename.endswith(".json"):
                    analysis_files.append(os.path.join(reports_dir, filename))
        
        if not analysis_files:
            # Try to find any recent analysis files as fallback
            if os.path.exists(reports_dir):
                all_analysis_files = [f for f in os.listdir(reports_dir) if f.startswith("analysis_report_") and f.endswith(".json")]
                if all_analysis_files:
                    # Get ALL analysis files, not just the most recent
                    analysis_files = [os.path.join(reports_dir, f) for f in all_analysis_files]
            
            if not analysis_files:
                return None
        
        # Aggregate analyses from all files
        all_analyses = []
        seen_urls = set()
        
        # Sort files by creation time (newest first) to prioritize recent data
        analysis_files.sort(key=os.path.getctime, reverse=True)
        
        print(f"DEBUG: Processing {len(analysis_files)} analysis files")
        
        for file_path in analysis_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    analysis_data = json.load(f)
                    analyses = analysis_data.get('analyses', [])
                    print(f"DEBUG: File {os.path.basename(file_path)} has {len(analyses)} analyses")
                    
                    # Add ALL analyses, but prioritize better quality ones
                    for analysis in analyses:
                        url = analysis.get('url', '')
                        if url:
                            # If we've seen this URL before, only replace if this analysis is better
                            if url in seen_urls:
                                # Find existing analysis and compare quality
                                for i, existing in enumerate(all_analyses):
                                    if existing.get('url') == url:
                                        # Replace if this analysis has better content
                                        current_score = analysis.get('risk_assessment', {}).get('score', 0)
                                        existing_score = existing.get('risk_assessment', {}).get('score', 0)
                                        current_summary_len = len(analysis.get('summary', ''))
                                        existing_summary_len = len(existing.get('summary', ''))
                                        
                                        if (current_score > existing_score or 
                                            (current_score == existing_score and current_summary_len > existing_summary_len)):
                                            all_analyses[i] = analysis
                                            print(f"DEBUG: Replaced analysis for {url} - Score: {existing_score} -> {current_score}, Title: {analysis.get('title', 'Unknown')}")
                                        break
                            else:
                                seen_urls.add(url)
                                all_analyses.append(analysis)
                                print(f"DEBUG: Added new analysis for {url}")
            except Exception as e:
                print(f"Error reading analysis file {file_path}: {e}")
                continue
        
        print(f"DEBUG: Returning {len(all_analyses)} total analyses")
        return all_analyses
            
    except Exception as e:
        print(f"Error loading analysis results: {e}")
        return None

@router.get("/crawl/{job_id}/pages")
async def get_crawl_pages(job_id: str):
    """Get crawled pages for a job"""
    pages = crawler_service.get_job_pages(job_id)
    if pages is None:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    return {"job_id": job_id, "pages": pages}

@router.get("/crawls", response_model=List[CrawlJob])
async def get_all_crawls():
    """Get all crawl jobs"""
    return list(crawler_service.active_jobs.values())

@router.get("/test-analysis")
async def test_analysis():
    """Test endpoint to show analysis results"""
    analysis_results = await get_analysis_results_for_job("test-job-id")
    return {
        "job_id": "test-job-id",
        "status": "completed",
        "total_links": 5,
        "crawled_links": 3,
        "analysis_results": analysis_results
    }

@router.get("/jobs")
async def list_crawl_jobs():
    """List all crawl jobs"""
    jobs = []
    for job_id, job in crawler_service.active_jobs.items():
        jobs.append({
            "id": job_id,
            "query": job.query,
            "status": job.status.value,
            "total_links": job.total_links,
            "crawled_links": job.crawled_links,
            "failed_links": job.failed_links,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat()
        })
    return {"jobs": jobs}

@router.delete("/crawl/{job_id}")
async def delete_crawl_job(job_id: str):
    """Delete a crawl job"""
    job = crawler_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    
    # Remove from active jobs
    if job_id in crawler_service.active_jobs:
        del crawler_service.active_jobs[job_id]
    
    return {"message": f"Crawl job {job_id} deleted successfully"}
