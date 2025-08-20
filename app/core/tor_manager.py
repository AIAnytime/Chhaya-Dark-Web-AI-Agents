import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class TorManager:
    def __init__(self):
        self.session = None
        self._setup_session()
    
    def _setup_session(self):
        """Initialize Tor session with proxy configuration"""
        self.session = requests.Session()
        
        # Configure proxies
        self.session.proxies = {
            'http': settings.TOR_SOCKS_PROXY,
            'https': settings.TOR_SOCKS_PROXY
        }
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def test_connection(self) -> dict:
        """Test Tor connection by checking IP"""
        try:
            response = self.session.get('http://httpbin.org/ip', timeout=10)
            return {
                "status": "connected",
                "ip": response.json().get("origin"),
                "message": "Tor connection successful"
            }
        except Exception as e:
            logger.error(f"Tor connection test failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "message": "Tor connection failed"
            }
    
    def get_session(self):
        """Get the configured Tor session"""
        return self.session
    
    def reset_session(self):
        """Reset the Tor session"""
        if self.session:
            self.session.close()
        self._setup_session()

# Global Tor manager instance
tor_manager = TorManager()
