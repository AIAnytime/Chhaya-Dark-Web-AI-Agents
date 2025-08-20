from fastapi import APIRouter, HTTPException
from app.models.schemas import MonitoringStats
from app.services.crawler_service import crawler_service
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/stats", response_model=MonitoringStats)
async def get_monitoring_stats():
    """Get overall monitoring statistics"""
    try:
        jobs = crawler_service.list_jobs()
        
        total_crawls = len(jobs)
        active_crawls = len([job for job in jobs if job.status == "in_progress"])
        total_pages_crawled = sum(len(job.pages) for job in jobs)
        
        # Risk distribution placeholder (would come from database in production)
        risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        # Recent activity
        recent_jobs = sorted(jobs, key=lambda x: x.updated_at, reverse=True)[:5]
        recent_activity = [
            {
                "job_id": job.id,
                "query": job.query,
                "status": job.status,
                "timestamp": job.updated_at.isoformat(),
                "pages_crawled": len(job.pages)
            }
            for job in recent_jobs
        ]
        
        return MonitoringStats(
            total_crawls=total_crawls,
            active_crawls=active_crawls,
            total_pages_crawled=total_pages_crawled,
            total_analyses=0,  # Would come from analysis service
            risk_distribution=risk_distribution,
            recent_activity=recent_activity
        )
    except Exception as e:
        logger.error(f"Failed to get monitoring stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Comprehensive health check"""
    from app.core.tor_manager import tor_manager
    
    health_status = {
        "service": "Chhaya OS",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Check Tor connection
    tor_status = tor_manager.test_connection()
    health_status["components"]["tor"] = {
        "status": "healthy" if tor_status["status"] == "connected" else "unhealthy",
        "details": tor_status
    }
    
    # Check file system
    try:
        from app.core.config import settings
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        health_status["components"]["filesystem"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["filesystem"] = {"status": "unhealthy", "error": str(e)}
    
    # Overall status
    unhealthy_components = [k for k, v in health_status["components"].items() if v["status"] == "unhealthy"]
    if unhealthy_components:
        health_status["status"] = "degraded"
        health_status["issues"] = unhealthy_components
    
    return health_status
