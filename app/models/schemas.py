from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class CrawlStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Request Models
class CrawlRequest(BaseModel):
    query: str = Field(..., description="Search query for dark web crawling")
    limit: Optional[int] = Field(10, description="Maximum number of sites to crawl")
    deep_crawl: Optional[bool] = Field(False, description="Enable deep crawling")

class AnalysisRequest(BaseModel):
    crawl_id: str = Field(..., description="ID of the crawl to analyze")
    analysis_type: Optional[str] = Field("full", description="Type of analysis to perform")

# Response Models
class TorStatus(BaseModel):
    status: str
    ip: Optional[str] = None
    message: str
    error: Optional[str] = None

class OnionLink(BaseModel):
    url: str
    title: Optional[str] = None
    engine: Optional[str] = None
    status: str = "discovered"

class CrawledPage(BaseModel):
    url: str
    title: Optional[str] = None
    text_content: str
    images: List[str] = []
    crawl_timestamp: datetime
    file_path: Optional[str] = None
    status: str = "crawled"

class RiskAssessment(BaseModel):
    score: int = Field(..., ge=0, le=100)
    level: RiskLevel
    category: str
    details: Optional[str] = None

class PIIData(BaseModel):
    names: List[str] = []
    emails: List[str] = []
    websites: List[str] = []
    contact_numbers: List[str] = []

class AIAnalysis(BaseModel):
    title: str
    url: str
    summary: str
    risk_assessment: RiskAssessment
    keywords: List[str] = []
    pii: PIIData
    action_plan: str
    analysis_timestamp: datetime

class CrawlJob(BaseModel):
    id: str
    query: str
    status: CrawlStatus
    created_at: datetime
    updated_at: datetime
    total_links: int = 0
    crawled_links: int = 0
    failed_links: int = 0
    pages: List[CrawledPage] = []
    error_message: Optional[str] = None

class CrawlResponse(BaseModel):
    job_id: str
    status: CrawlStatus
    message: str
    total_links: Optional[int] = None
    crawled_pages: Optional[int] = None

class AnalysisResponse(BaseModel):
    job_id: str
    crawl_id: str
    status: str
    analyses: List[AIAnalysis] = []
    summary_stats: Optional[Dict[str, Any]] = None

class MonitoringStats(BaseModel):
    total_crawls: int
    active_crawls: int
    total_pages_crawled: int
    total_analyses: int
    risk_distribution: Dict[str, int]
    recent_activity: List[Dict[str, Any]] = []
