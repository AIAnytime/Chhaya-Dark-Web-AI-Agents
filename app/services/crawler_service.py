import subprocess
import csv
import os
import hashlib
import time
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.tor_manager import tor_manager
from app.models.schemas import CrawlJob, CrawledPage, OnionLink, CrawlStatus
import logging

logger = logging.getLogger(__name__)

class CrawlerService:
    def __init__(self):
        self.active_jobs: Dict[str, CrawlJob] = {}
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure output directories exist"""
        os.makedirs(settings.PAGES_DIR, exist_ok=True)
        os.makedirs(settings.SUMMARY_DIR, exist_ok=True)
        os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    
    async def start_crawl(self, query: str, limit: int = None) -> str:
        """Start a new crawl job"""
        # Check for existing active job with same query to prevent duplicates
        for existing_job in self.active_jobs.values():
            if (existing_job.query == query and 
                existing_job.status in [CrawlStatus.PENDING, CrawlStatus.IN_PROGRESS]):
                logger.info(f"Returning existing job {existing_job.id} for query: {query}")
                return existing_job.id
        
        job_id = str(uuid.uuid4())
        limit = limit or settings.DEFAULT_CRAWL_LIMIT
        
        job = CrawlJob(
            id=job_id,
            query=query,
            status=CrawlStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.active_jobs[job_id] = job
        
        # Start crawling in background using asyncio.create_task for non-blocking execution
        import asyncio
        asyncio.create_task(self._execute_crawl_background(job_id, query, limit))
        
        return job_id
    
    async def _execute_crawl_background(self, job_id: str, query: str, limit: int):
        """Execute crawl in background without blocking the API response"""
        try:
            await self._execute_crawl(job_id, query, limit)
        except Exception as e:
            logger.error(f"Crawl job {job_id} failed: {e}")
            job = self.active_jobs.get(job_id)
            if job:
                job.status = CrawlStatus.FAILED
                job.error_message = str(e)
                job.updated_at = datetime.now()
    
    async def _execute_crawl(self, job_id: str, query: str, limit: int):
        """Execute the crawl job"""
        job = self.active_jobs[job_id]
        job.status = CrawlStatus.IN_PROGRESS
        job.updated_at = datetime.now()
        
        try:
            # Step 1: Run OnionSearch
            csv_file = await self._run_onionsearch(query, limit)
            
            # Step 2: Extract onion links from the limited CSV file
            all_onion_links = await self._extract_onion_links(csv_file)
            job.total_links = len(all_onion_links)
            
            # Step 3: Use all links from the limited file (already per-engine limited)
            links_to_crawl = all_onion_links
            logger.info(f"Using {len(all_onion_links)} per-engine limited links for crawling")
            
            # Step 4: Crawl each link (up to the limit)
            for i, link in enumerate(links_to_crawl):
                try:
                    logger.info(f"Crawling {i+1}/{len(links_to_crawl)}: {link.url}")
                    page = await self._crawl_page(link.url)
                    if page:
                        job.pages.append(page)
                        job.crawled_links += 1
                    else:
                        job.failed_links += 1
                    
                    job.updated_at = datetime.now()
                    
                    # Politeness delay
                    time.sleep(settings.CRAWL_DELAY)
                    
                except Exception as e:
                    logger.error(f"Failed to crawl {link.url}: {e}")
                    job.failed_links += 1
            
            job.status = CrawlStatus.COMPLETED
            job.updated_at = datetime.now()
            
            # Trigger AI analysis if we have crawled pages
            if job.pages:
                logger.info(f"Triggering AI analysis for job {job_id} with {len(job.pages)} pages")
                await self._trigger_ai_analysis(job_id)
            
        except Exception as e:
            job.status = CrawlStatus.FAILED
            job.error_message = str(e)
            job.updated_at = datetime.now()
    
    async def _run_onionsearch(self, query: str, limit: int) -> str:
        """Run OnionSearch command with per-engine limiting"""
        safe_query = query.replace(" ", "_")
        output_file = f"{settings.OUTPUT_DIR}/onionsearch_{safe_query}.csv"
        
        logger.info(f"Running OnionSearch for: {query}")
        
        # Use configurable per-engine limit to prevent massive results
        per_engine_limit = settings.ONIONSEARCH_PER_ENGINE_LIMIT
        
        subprocess.run([
            "onionsearch",
            query,
            "--proxy", f"{settings.TOR_PROXY_HOST}:{settings.TOR_PROXY_PORT}",
            "--output", output_file,
            "--limit", str(per_engine_limit)
        ])
        
        # Post-process to manually limit results per engine since OnionSearch --limit doesn't work properly
        limited_output_file = await self._limit_results_per_engine(output_file, per_engine_limit)
        
        return limited_output_file
    
    async def _trigger_ai_analysis(self, job_id: str):
        """Trigger AI analysis for completed crawl job"""
        try:
            from ..services.ai_service import ai_service
            
            job = self.active_jobs.get(job_id)
            if not job or not job.pages:
                return
            
            # Start AI analysis in background
            import asyncio
            asyncio.create_task(ai_service.analyze_crawl_job(job_id, job.pages))
            logger.info(f"AI analysis started for job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to trigger AI analysis for job {job_id}: {e}")
    
    async def _limit_results_per_engine(self, csv_file: str, per_engine_limit: int) -> str:
        """Manually limit results per engine since OnionSearch --limit doesn't work properly"""
        try:
            import csv
            from collections import defaultdict
            
            # Read original results
            engine_results = defaultdict(list)
            
            try_encodings = ['utf-8', 'windows-1252']
            for enc in try_encodings:
                try:
                    with open(csv_file, 'r', encoding=enc) as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if len(row) >= 3:  # engine, name, link
                                engine = row[0]
                                engine_results[engine].append(row)
                    break
                except UnicodeDecodeError:
                    continue
            
            # Limit results per engine
            limited_results = []
            total_limited = 0
            
            for engine, results in engine_results.items():
                limited = results[:per_engine_limit]
                limited_results.extend(limited)
                total_limited += len(limited)
                logger.info(f"Engine {engine}: {len(results)} -> {len(limited)} results")
            
            # Write limited results to new file
            limited_file = csv_file.replace('.csv', '_limited.csv')
            with open(limited_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(limited_results)
            
            logger.info(f"Limited results: {total_limited} total links from {len(engine_results)} engines")
            return limited_file
            
        except Exception as e:
            logger.error(f"Failed to limit results: {e}")
            return csv_file  # Return original file if limiting fails
    
    async def _extract_onion_links(self, file_path: str) -> List[OnionLink]:
        """Extract onion links from CSV file"""
        links = []
        try_encodings = ['utf-8', 'windows-1252']
        
        for enc in try_encodings:
            try:
                with open(file_path, encoding=enc) as f:
                    lines = f.readlines()
                    first_row = lines[0].strip().split(',')
                    
                    # Detect if header is missing
                    if '.onion' in first_row[-1]:
                        logger.info("No header detected. Injecting fallback header")
                        lines.insert(0, "engine,name,link\n")
                    
                    reader = csv.DictReader(lines)
                    for row in reader:
                        if '.onion' in row.get('link', ''):
                            links.append(OnionLink(
                                url=row['link'],
                                title=row.get('name', ''),
                                engine=row.get('engine', '')
                            ))
                break
            except UnicodeDecodeError:
                logger.warning(f"Encoding {enc} failed. Trying next...")
        
        unique_links = list({link.url: link for link in links}.values())
        logger.info(f"Extracted {len(unique_links)} unique .onion URLs")
        return unique_links
    
    async def _crawl_page(self, url: str) -> Optional[CrawledPage]:
        """Crawl a single page"""
        try:
            logger.info(f"Crawling: {url}")
            session = tor_manager.get_session()
            
            response = session.get(url, timeout=settings.REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content
            text = soup.get_text(separator=' ', strip=True)[:settings.MAX_TEXT_LENGTH]
            images = [img['src'] for img in soup.find_all('img') if img.get('src')][:settings.MAX_IMAGES]
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # Save to file
            file_path = await self._save_page_content(url, text, images)
            
            page = CrawledPage(
                url=url,
                title=title_text,
                text_content=text,
                images=images,
                crawl_timestamp=datetime.now(),
                file_path=file_path
            )
            
            logger.info(f"Successfully crawled: {url}")
            return page
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return None
    
    async def _save_page_content(self, url: str, text: str, images: List[str]) -> str:
        """Save page content to file"""
        hostname = urlparse(url).hostname or "unknown"
        uid = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"{hostname}_{uid}.txt"
        filepath = os.path.join(settings.PAGES_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"URL: {url}\n\n")
            f.write("Text Content:\n")
            f.write(text + "\n\n")
            f.write("Image Links:\n")
            for img in images:
                f.write(f"{img}\n")
        
        return filepath
    
    def get_job_status(self, job_id: str) -> Optional[CrawlJob]:
        """Get status of a crawl job"""
        return self.active_jobs.get(job_id)
    
    def list_jobs(self) -> List[CrawlJob]:
        """List all crawl jobs"""
        return list(self.active_jobs.values())
    
    def get_job_pages(self, job_id: str) -> List[CrawledPage]:
        """Get crawled pages for a job"""
        job = self.active_jobs.get(job_id)
        return job.pages if job else []

# Global crawler service instance
crawler_service = CrawlerService()
