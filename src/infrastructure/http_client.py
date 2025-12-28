"""Infrastructure HTTP Client - Download com Retry"""

import logging
import httpx
from retry import retry
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class HttpDownloader:
    """Cliente HTTP para download de PDFs com retry automático"""

    PDF_URL_TEMPLATE = "http://arquivopessoa.net/typographia/textos/arquivopessoa-{}.pdf"
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/pdf",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": "http://arquivopessoa.net",
        "Connection": "keep-alive",
    }

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Context manager entry"""
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.DEFAULT_HEADERS
        )
        logger.info("✓ HTTP Client inicializado")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.client:
            await self.client.aclose()
        logger.info("✓ HTTP Client fechado")

    @retry(tries=3, delay=2, backoff=2, logger=logger, exceptions=(httpx.HTTPError, httpx.ReadTimeout, Exception))
    async def download(self, poema_id: int) -> bytes:
        """
        Faz download de um PDF com retry automático.
        
        Args:
            poema_id: ID do poema
            
        Returns:
            Conteúdo do PDF em bytes
            
        Raises:
            httpx.HTTPError: Se falhar após 3 tentativas
        """
        if not self.client:
            raise RuntimeError("HttpDownloader não foi inicializado. Use com context manager.")

        url = self.PDF_URL_TEMPLATE.format(poema_id)
        
        try:
            logger.debug(f"Downloading: {url}")
            response = await self.client.get(url)
            response.raise_for_status()
            logger.debug(f"✓ Download concluído: {len(response.content)} bytes")
            return response.content
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code} para poema {poema_id}")
            raise
        except Exception as e:
            logger.error(f"Erro ao baixar poema {poema_id}: {e}")
            raise

    async def download_and_save(self, poema_id: int, save_path: Path) -> None:
        """
        Faz download de um PDF e salva em arquivo.
        
        Args:
            poema_id: ID do poema
            save_path: Caminho onde salvar o PDF
        """
        save_path.parent.mkdir(parents=True, exist_ok=True)
        content = await self.download(poema_id)
        save_path.write_bytes(content)
        logger.info(f"✓ Salvo: {save_path.name}")
