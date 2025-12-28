"""Configuration and Factory Functions"""

from pathlib import Path
from typing import Optional
from src.infrastructure.browser import PlaywrightBrowser
from src.infrastructure.parser import HtmlParserAdapter
from src.infrastructure.http_client import HttpDownloader
from src.infrastructure.repositories import (
    JsonStructureRepository,
    PdfFileRepository
)
from src.application.scraper_service import WebScraperService
from src.application.filter_service import FilterService
from src.application.download_service import DownloadService
from src.application.structure_service import StructureService
from src.application.persistence_service import PersistenceService


class DIContainer:
    """Dependency Injection Container - Factory para dependências"""

    @staticmethod
    def create_scraper_service(headless: bool = False) -> WebScraperService:
        """Factory para WebScraperService"""
        browser = PlaywrightBrowser(headless=headless)
        parser = HtmlParserAdapter()
        return WebScraperService(browser, parser)

    @staticmethod
    def create_download_service(
        base_path: Path,
        min_delay: float = 3.0,
        max_delay: float = 7.0
    ) -> DownloadService:
        """Factory para DownloadService"""
        http_downloader = HttpDownloader()
        pdf_repo = PdfFileRepository(base_path)
        return DownloadService(http_downloader, pdf_repo, base_path, min_delay, max_delay)

    @staticmethod
    def create_persistence_service() -> PersistenceService:
        """Factory para PersistenceService"""
        json_repo = JsonStructureRepository()
        return PersistenceService(json_repo)

    @staticmethod
    def create_filter_service(base_path: Path) -> FilterService:
        """Factory para FilterService"""
        return FilterService(base_path)

    @staticmethod
    def create_structure_service() -> StructureService:
        """Factory para StructureService"""
        json_repo = JsonStructureRepository()
        return StructureService(json_repo)
