"""Application Download Service - Gerenciamento de Downloads"""

import asyncio
import logging
import random
from pathlib import Path
from typing import Optional
from src.domain.models import Categoria
from src.infrastructure.http_client import HttpDownloader
from src.infrastructure.repositories import PdfFileRepository
from src.application.progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)


class DownloadService:
    """Serviço para gerenciar downloads de PDFs com retry e delays"""

    def __init__(
        self,
        http_downloader: HttpDownloader,
        file_repository: PdfFileRepository,
        base_path: Path,
        min_delay: float = 3.0,
        max_delay: float = 7.0
    ):
        self.http_downloader = http_downloader
        self.file_repository = file_repository
        self.base_path = base_path or Path("arquivos_pessoa")
        self.min_delay = min_delay
        self.max_delay = max_delay

    async def download_categoria_recursively(
        self,
        categoria: Categoria,
        progress_tracker: ProgressTracker
    ) -> None:
        """
        Baixa poemas de uma categoria recursivamente com delays.
        
        Args:
            categoria: Categoria com poemas a baixar
            progress_tracker: Rastreador de progresso
        """
        # Criar pasta da categoria
        categoria_dir = self.base_path / categoria.path
        categoria_dir.mkdir(parents=True, exist_ok=True)

        # Baixar poemas desta categoria
        if categoria.poemas:
            logger.info(f"Baixando {len(categoria.poemas)} poemas de '{categoria.nome}'...")

            for poema in categoria.poemas:
                pdf_filename = f"{poema.id:04d} - {poema.titulo}.pdf"
                pdf_path = categoria_dir / pdf_filename

                try:
                    await self.http_downloader.download_and_save(poema.id, pdf_path)
                    progress_tracker.increment(pdf_filename)
                except Exception as e:
                    logger.error(f"  ✗ [{progress_tracker.atual + 1:04d}/{progress_tracker.total:04d}] {pdf_filename}: {e}")
                    progress_tracker.increment()  # Incrementar mesmo com erro

                # Delay aleatório entre downloads
                delay = random.uniform(self.min_delay, self.max_delay)
                await asyncio.sleep(delay)

        # Processar subcategorias recursivamente
        for subcategoria in categoria.subcategorias:
            await self.download_categoria_recursively(subcategoria, progress_tracker)

    async def download_all_poemas(
        self,
        categoria: Categoria,
        progress_tracker: Optional[ProgressTracker] = None
    ) -> None:
        """
        Baixa todos os poemas de uma categoria.
        
        Args:
            categoria: Categoria com poemas a baixar
            progress_tracker: Rastreador de progresso (opcional)
        """
        if progress_tracker is None:
            from .structure_service import StructureService
            total = StructureService.count_poemas_recursively(categoria)
            progress_tracker = ProgressTracker(total)

        await self.download_categoria_recursively(categoria, progress_tracker)
