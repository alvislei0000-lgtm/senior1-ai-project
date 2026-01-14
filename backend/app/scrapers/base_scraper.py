"""
基礎爬蟲類別
遵守 robots.txt 與 rate limiting
"""
import os
import asyncio
import time
from typing import Optional, Dict, Any
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import httpx
from datetime import datetime

class BaseScraper:
    """基礎爬蟲類別，提供 robots.txt 檢查與 rate limiting"""
    
    def __init__(self):
        self.base_url: Optional[str] = None
        self.robots_parser: Optional[RobotFileParser] = None
        self.last_request_time: float = 0
        self.request_delay: float = float(
            os.getenv("REQUEST_DELAY_SECONDS", "1.0")
        )
        self.user_agent = "HardwareBenchmarkBot/1.0 (+https://github.com/your-repo)"
        self.client: Optional[httpx.AsyncClient] = None
        
    async def initialize(self):
        """初始化 HTTP 客戶端與 robots.txt"""
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": self.user_agent},
            follow_redirects=True
        )
        
        if self.base_url:
            await self._load_robots_txt()
    
    async def _load_robots_txt(self):
        """載入並解析 robots.txt"""
        try:
            robots_url = urljoin(self.base_url, "/robots.txt")
            self.robots_parser = RobotFileParser()
            self.robots_parser.set_url(robots_url)
            self.robots_parser.read()
        except Exception as e:
            print(f"無法載入 robots.txt: {e}")
            # 如果無法載入，假設允許所有請求但使用較長的延遲
            self.request_delay = 2.0
    
    def can_fetch(self, url: str) -> bool:
        """檢查是否允許抓取指定 URL"""
        if not self.robots_parser:
            return True
        return self.robots_parser.can_fetch(self.user_agent, url)
    
    async def _rate_limit(self):
        """實作 rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    async def fetch(self, url: str, **kwargs) -> Optional[httpx.Response]:
        """
        安全地抓取網頁，遵守 robots.txt 與 rate limiting
        """
        if not self.can_fetch(url):
            raise Exception(f"robots.txt 不允許抓取: {url}")
        
        await self._rate_limit()
        
        if not self.client:
            await self.initialize()
        
        try:
            response = await self.client.get(url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            print(f"HTTP 錯誤: {url} - {e}")
            return None
    
    async def close(self):
        """關閉 HTTP 客戶端"""
        if self.client:
            await self.client.aclose()
    
    def get_source_name(self) -> str:
        """取得來源名稱（子類別需實作）"""
        raise NotImplementedError
    
    def get_last_fetch_time(self) -> str:
        """取得最後抓取時間"""
        return datetime.now().isoformat()

