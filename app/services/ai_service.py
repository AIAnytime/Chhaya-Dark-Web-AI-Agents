import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from google import genai

from app.core.config import settings
from app.models.schemas import AIAnalysis, RiskAssessment, PIIData, RiskLevel
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL
    
    def build_analysis_prompt(self, text: str, url: str) -> str:
        """Build prompt for AI analysis"""
        return f"""
You are a darknet/darkweb intelligence analyst for Chhaya OS.

Given the raw content of a darknet page, analyze and return a report in JSON format with the following keys:

- title: string (extracted or inferred page title)
- url: string (the page URL)
- summary: string (concise summary of page content)
- risk_assessment: object with:
  - score: integer (0-100, where 100 is highest risk)
  - level: string (low/medium/high/critical)
  - category: string (type of threat/content)
- keywords: array of strings (key terms found)
- pii: object with:
  - names: array of person names found
  - emails: array of email addresses
  - websites: array of website URLs
  - contact_numbers: array of phone numbers
- action_plan: string (recommended actions based on analysis)

Darknet page content:
{text}

Page URL:
{url}

⚠️ Please return only valid JSON. Do not use markdown, triple backticks, or any explanation. The response must start with {{ and end with }}.
"""
    
    async def analyze_page(self, url: str, text_content: str) -> Optional[AIAnalysis]:
        """Analyze a single page using AI"""
        try:
            prompt = self.build_analysis_prompt(text_content, url)
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            output_text = response.text.strip()
            
            # Clean markdown if wrapped
            if output_text.startswith("```json"):
                output_text = output_text.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON response
            data = json.loads(output_text)
            
            # Convert to structured models
            risk_assessment = RiskAssessment(
                score=data['risk_assessment']['score'],
                level=RiskLevel(data['risk_assessment']['level']),
                category=data['risk_assessment']['category']
            )
            
            pii_data = PIIData(
                names=data['pii'].get('names', []),
                emails=data['pii'].get('emails', []),
                websites=data['pii'].get('websites', []),
                contact_numbers=data['pii'].get('contact_numbers', [])
            )
            
            analysis = AIAnalysis(
                title=data['title'],
                url=data['url'],
                summary=data['summary'],
                risk_assessment=risk_assessment,
                keywords=data.get('keywords', []),
                pii=pii_data,
                action_plan=data['action_plan'],
                analysis_timestamp=datetime.now()
            )
            
            logger.info(f"Successfully analyzed page: {url}")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze page {url}: {e}")
            return None
    
    async def batch_analyze_pages(self, pages: List[Dict[str, str]]) -> List[AIAnalysis]:
        """Analyze multiple pages in batch"""
        analyses = []
        
        for page in pages:
            try:
                analysis = await self.analyze_page(page['url'], page['text_content'])
                if analysis:
                    analyses.append(analysis)
                
                # Rate limiting delay
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"Batch analysis failed for {page['url']}: {e}")
        
        return analyses
    
    async def generate_summary_report(self, analyses: List[AIAnalysis]) -> Dict:
        """Generate summary report from multiple analyses"""
        if not analyses:
            return {"error": "No analyses provided"}
        
        # Calculate statistics
        total_analyses = len(analyses)
        risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        all_keywords = []
        high_risk_pages = []
        
        for analysis in analyses:
            risk_level = analysis.risk_assessment.level.value
            risk_distribution[risk_level] += 1
            all_keywords.extend(analysis.keywords)
            
            if risk_level in ["high", "critical"]:
                high_risk_pages.append({
                    "url": analysis.url,
                    "title": analysis.title,
                    "risk_score": analysis.risk_assessment.score,
                    "category": analysis.risk_assessment.category
                })
        
        # Count keyword frequency
        keyword_freq = {}
        for keyword in all_keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        summary = {
            "total_pages_analyzed": total_analyses,
            "risk_distribution": risk_distribution,
            "high_risk_pages": high_risk_pages,
            "top_keywords": [{"keyword": k, "frequency": f} for k, f in top_keywords],
            "analysis_timestamp": datetime.now().isoformat(),
            "recommendations": self._generate_recommendations(risk_distribution, high_risk_pages)
        }
        
        return summary
    
    def _generate_recommendations(self, risk_distribution: Dict, high_risk_pages: List) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if risk_distribution["critical"] > 0:
            recommendations.append("CRITICAL: Immediate attention required for critical risk pages")
        
        if risk_distribution["high"] > 0:
            recommendations.append("HIGH: Monitor high-risk pages closely")
        
        if len(high_risk_pages) > 5:
            recommendations.append("Consider implementing automated monitoring for high-risk domains")
        
        if risk_distribution["low"] > risk_distribution["high"] + risk_distribution["critical"]:
            recommendations.append("Overall risk level appears manageable")
        
        return recommendations
    
    async def save_analysis_report(self, analyses: List[AIAnalysis], crawl_id: str) -> str:
        """Save analysis report to file"""
        report_data = {
            "crawl_id": crawl_id,
            "timestamp": datetime.now().isoformat(),
            "analyses": [analysis.dict() for analysis in analyses],
            "summary": await self.generate_summary_report(analyses)
        }
        
        filename = f"analysis_report_{crawl_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(settings.REPORTS_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Analysis report saved: {filepath}")
        return filepath

    async def analyze_crawl_job(self, job_id: str, pages: List[Dict]) -> None:
        """Analyze pages from a crawl job and save results"""
        try:
            logger.info(f"Starting AI analysis for job {job_id} with {len(pages)} pages")
            
            # Convert pages to the expected format
            formatted_pages = []
            for page in pages:
                if hasattr(page, 'url') and hasattr(page, 'text_content'):
                    # Page is a CrawledPage object
                    formatted_pages.append({
                        'url': page.url,
                        'text_content': page.text_content
                    })
                else:
                    # Page is a dictionary
                    formatted_pages.append({
                        'url': page.get('url', ''),
                        'text_content': page.get('text_content', '')
                    })
            
            # Perform batch analysis
            analyses = await self.batch_analyze_pages(formatted_pages)
            
            if analyses:
                # Generate and save summary report
                summary_report = await self.generate_summary_report(analyses)
                await self.save_analysis_report(job_id, summary_report, analyses)
                logger.info(f"AI analysis completed for job {job_id}: {len(analyses)} pages analyzed")
            else:
                logger.warning(f"No successful analyses for job {job_id}")
                
        except Exception as e:
            logger.error(f"Failed to analyze crawl job {job_id}: {e}")

# Global AI service instance
ai_service = AIService()
