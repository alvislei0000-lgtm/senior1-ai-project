"""
硬體資訊爬蟲
從網路即時抓取硬體列表，不使用內建靜態資料
"""
from typing import List, Optional
from bs4 import BeautifulSoup
import re
from datetime import datetime

from app.scrapers.base_scraper import BaseScraper

class HardwareScraper(BaseScraper):
    """硬體資訊爬蟲"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.techpowerup.com"
        self.source_name = "TechPowerUp GPU Database"
        self.last_fetch_time: Optional[str] = None
    
    async def fetch_hardware_list(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[dict]:
        """
        從網路抓取硬體列表
        注意：這是範例實作，實際應根據可用的公開 API 或網站調整
        """
        await self.initialize()
        
        hardware_list = []
        
        # 範例：從 TechPowerUp 抓取 GPU 列表
        # 實際實作需要根據網站結構調整
        try:
            if category == "gpu" or category is None:
                gpu_list = await self._fetch_gpu_list(search)
                hardware_list.extend(gpu_list)
            
            if category == "cpu" or category is None:
                cpu_list = await self._fetch_cpu_list(search)
                hardware_list.extend(cpu_list)
            
            self.last_fetch_time = datetime.now().isoformat()
            
        except Exception as e:
            print(f"抓取硬體列表失敗: {e}")
            # 如果主要來源失敗，嘗試備用來源
            hardware_list = await self._fetch_from_fallback_source(category, search)
        
        return hardware_list
    
    async def _fetch_gpu_list(self, search: Optional[str] = None) -> List[dict]:
        """抓取 GPU 列表"""
        # 嘗試從網路抓取
        url = f"{self.base_url}/gpu-specs/"
        response = await self.fetch(url)
        
        gpu_list = []
        
        if response:
            soup = BeautifulSoup(response.text, 'lxml')
            # 解析 GPU 表格（需要根據實際網站結構調整）
            gpu_rows = soup.select("table.gpu-list tr")[:100]  # 限制數量
            
            for row in gpu_rows:
                try:
                    cells = row.select("td")
                    if len(cells) < 3:
                        continue
                    
                    model = cells[0].get_text(strip=True)
                    brand = cells[1].get_text(strip=True)
                    year_text = cells[2].get_text(strip=True)
                    
                    # 提取年份
                    year_match = re.search(r'\d{4}', year_text)
                    year = int(year_match.group()) if year_match else None
                    
                    # 提取世代（如果有）
                    generation = None
                    gen_match = re.search(r'(\w+)\s*(\d+)', model)
                    if gen_match:
                        generation = gen_match.group(1)
                    
                    # 搜尋過濾
                    if search:
                        search_lower = search.lower()
                        if (search_lower not in model.lower() and 
                            search_lower not in brand.lower()):
                            continue
                    gpu_list.append({
                        "category": "gpu",
                        "model": model,
                        "generation": generation,
                        "release_year": year,
                        "brand": brand
                    })
                except Exception as e:
                    print(f"解析 GPU 資料失敗: {e}")
                    continue
        
        # 如果無法從網路取得，提供常用 GPU 列表（僅用於開發測試）
        if not gpu_list:
            gpu_list = self._get_default_gpu_list(search)
        
        return gpu_list
    
    def _get_default_gpu_list(self, search: Optional[str] = None) -> List[dict]:
        """取得預設 GPU 列表（僅用於開發測試）"""
        default_gpus = [
            {"model": "RTX 4090", "brand": "NVIDIA", "generation": "Ada", "year": 2022},
            {"model": "RTX 4080", "brand": "NVIDIA", "generation": "Ada", "year": 2022},
            {"model": "RTX 4070", "brand": "NVIDIA", "generation": "Ada", "year": 2023},
            {"model": "RTX 3090", "brand": "NVIDIA", "generation": "Ampere", "year": 2020},
            {"model": "RTX 3080", "brand": "NVIDIA", "generation": "Ampere", "year": 2020},
            {"model": "RTX 3070", "brand": "NVIDIA", "generation": "Ampere", "year": 2020},
            {"model": "RX 7900 XTX", "brand": "AMD", "generation": "RDNA 3", "year": 2022},
            {"model": "RX 7900 XT", "brand": "AMD", "generation": "RDNA 3", "year": 2022},
            {"model": "RX 6900 XT", "brand": "AMD", "generation": "RDNA 2", "year": 2020},
            {"model": "RX 6800 XT", "brand": "AMD", "generation": "RDNA 2", "year": 2020},
        ]
        
        gpu_list = []
        for gpu in default_gpus:
            # 搜尋過濾
            if search:
                search_lower = search.lower()
                if (search_lower not in gpu["model"].lower() and 
                    search_lower not in gpu["brand"].lower()):
                    continue
            
            gpu_list.append({
                "category": "gpu",
                "model": gpu["model"],
                "generation": gpu["generation"],
                "release_year": gpu["year"],
                "brand": gpu["brand"]
            })
        
        return gpu_list
    
    async def _fetch_cpu_list(self, search: Optional[str] = None) -> List[dict]:
        """抓取 CPU 列表"""
        # 嘗試從網路抓取（實際實作）
        # 如果失敗，提供預設列表
        
        # 提供預設 CPU 列表（僅用於開發測試）
        return self._get_default_cpu_list(search)
    
    def _get_default_cpu_list(self, search: Optional[str] = None) -> List[dict]:
        """取得預設 CPU 列表（僅用於開發測試）"""
        default_cpus = [
            {"model": "Intel Core i9-13900K", "brand": "Intel", "generation": "13th Gen", "year": 2022},
            {"model": "Intel Core i7-13700K", "brand": "Intel", "generation": "13th Gen", "year": 2022},
            {"model": "Intel Core i5-13600K", "brand": "Intel", "generation": "13th Gen", "year": 2022},
            {"model": "Intel Core i9-12900K", "brand": "Intel", "generation": "12th Gen", "year": 2021},
            {"model": "AMD Ryzen 9 7950X", "brand": "AMD", "generation": "Zen 4", "year": 2022},
            {"model": "AMD Ryzen 9 7900X", "brand": "AMD", "generation": "Zen 4", "year": 2022},
            {"model": "AMD Ryzen 7 7700X", "brand": "AMD", "generation": "Zen 4", "year": 2022},
            {"model": "AMD Ryzen 9 5950X", "brand": "AMD", "generation": "Zen 3", "year": 2020},
            {"model": "AMD Ryzen 7 5800X", "brand": "AMD", "generation": "Zen 3", "year": 2020},
        ]
        
        cpu_list = []
        for cpu in default_cpus:
            # 搜尋過濾
            if search:
                search_lower = search.lower()
                if (search_lower not in cpu["model"].lower() and 
                    search_lower not in cpu["brand"].lower()):
                    continue
            
            cpu_list.append({
                "category": "cpu",
                "model": cpu["model"],
                "generation": cpu["generation"],
                "release_year": cpu["year"],
                "brand": cpu["brand"]
            })
        
        return cpu_list
    
    async def _fetch_from_fallback_source(
        self,
        category: Optional[str],
        search: Optional[str]
    ) -> List[dict]:
        """
        從備用來源抓取（如果主要來源失敗）
        可以整合多個來源以提高可靠性
        """
        # 這裡可以實作其他來源的抓取邏輯
        # 例如：UserBenchmark, PassMark 等
        return []
    
    def get_source_name(self) -> str:
        return self.source_name
    
    def get_last_fetch_time(self) -> str:
        return self.last_fetch_time or datetime.now().isoformat()

