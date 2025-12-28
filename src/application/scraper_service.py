"""Application Services - Serviços de Negócio"""

import logging
from typing import Optional
from src.domain.models import Categoria, StructureCatalog
from src.infrastructure.browser import PlaywrightBrowser
from src.infrastructure.parser import HtmlParserAdapter

logger = logging.getLogger(__name__)


class WebScraperService:
    """Serviço para scraping da web com Playwright e parsing"""

    def __init__(
        self,
        browser: PlaywrightBrowser,
        parser: HtmlParserAdapter
    ):
        self.browser = browser
        self.parser = parser

    async def fetch_and_extract_structure(self) -> StructureCatalog:
        """
        Realiza scraping completo e extrai estrutura de categorias.
        
        Returns:
            Catálogo com todas as categorias e poemas
        """
        logger.info("[1] Acessando página e expandindo categorias...")
        html = await self.browser.fetch_with_javascript()

        logger.info("[2] Extraindo categorias do HTML...")
        categorias = self.parser.parse_categories(html)
        logger.info(f"✓ {len(categorias)} categorias principais encontradas")

        logger.info("[3] Contabilizando poemas...")
        catalog = StructureCatalog.from_categorias(categorias)
        logger.info(f"📊 Total: {catalog.total_poemas} poemas extraídos")

        return catalog
