"""Main Scraper - Script Principal de Scraping com Clean Architecture"""

import asyncio
import logging

from pathlib import Path
from config import DIContainer
from src.application.progress_tracker import ProgressTracker
from src.utils.logger import setup_logging

# Configurar logging
logger = setup_logging("scraper", logging.INFO)


async def main():
    """Orquestração principal do scraper"""
    
    logger.info("🚀 Iniciando scraper do Arquivo Pessoa (Clean Architecture)")
    
    try:
        # Fase 1: Web Scraping e Extração
        logger.info("\n" + "="*60)
        logger.info("FASE 1: Web Scraping e Extração de Estrutura")
        logger.info("="*60)

        scraper_service = DIContainer.create_scraper_service(headless=False)
        async with scraper_service.browser:
            catalog = await scraper_service.fetch_and_extract_structure()

        # Fase 2: Persistência de Estrutura
        logger.info("\n" + "="*60)
        logger.info("FASE 2: Persistência de Estrutura")
        logger.info("="*60)

        persistence_service = DIContainer.create_persistence_service()
        await persistence_service.save_catalog(catalog, Path("arquivos_pessoa"))

        # Fase 3: Download de PDFs
        logger.info("\n" + "="*60)
        logger.info("FASE 3: Download de Arquivos PDF")
        logger.info("="*60)

        download_service = DIContainer.create_download_service(Path("arquivos_pessoa"), min_delay=2.0, max_delay=2.3)
        async with download_service.http_downloader:
            # Criar rastreador de progresso
            progress_tracker = ProgressTracker(catalog.total_poemas)

            # Baixar todos os poemas
            logger.info(f"📊 Total: {catalog.total_poemas} poemas para baixar\n")
            
            for categoria in catalog.categorias:
                await download_service.download_all_poemas(categoria, progress_tracker)

        logger.info("\n" + "="*60)
        logger.info("✅ Scraper concluído com sucesso!")
        logger.info("="*60)
        logger.info(f"📊 Resumo: {progress_tracker.get_summary()}")

    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
