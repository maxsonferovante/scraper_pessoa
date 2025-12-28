"""Main Download - Script de Download Resumível com Clean Architecture"""

import asyncio
import logging
from pathlib import Path
from config import DIContainer
from src.application.progress_tracker import ProgressTracker
from src.utils.logger import setup_logging

# Configurar logging
logger = setup_logging("download", logging.INFO)


async def main():
    """Orquestração principal de downloads resumíveis"""
    
    logger.info("🔄 Iniciando download resumível de poemas faltantes")
    
    try:
        # Fase 1: Carregar estrutura existente
        logger.info("\n" + "="*60)
        logger.info("FASE 1: Carregando Estrutura Existente")
        logger.info("="*60)

        persistence_service = DIContainer.create_persistence_service()
        
        try:
            catalog = await persistence_service.load_catalog()
            logger.info(f"✓ {catalog.total_categorias} categorias carregadas")
        except FileNotFoundError as e:
            logger.error(f"❌ {e}")
            logger.info("💡 Execute primeiro: python src/main_scraper.py")
            return

        # Fase 2: Filtrar poemas faltantes
        logger.info("\n" + "="*60)
        logger.info("FASE 2: Identificando Poemas Faltantes")
        logger.info("="*60)

        filter_service = DIContainer.create_filter_service(Path("arquivos_pessoa"))
        
        categorias_faltantes = []
        for categoria in catalog.categorias:
            cat_filtrada = filter_service.filter_missing_poemas(categoria)
            if cat_filtrada:
                categorias_faltantes.append(cat_filtrada)

        if not categorias_faltantes:
            logger.info("✅ Nenhum poema faltante encontrado!")
            return

        # Contar total de poemas faltantes
        total_faltantes = 0
        for categoria in categorias_faltantes:
            total_faltantes += filter_service.count_missing_poemas(categoria)

        logger.info(f"📊 Total de {total_faltantes} poemas para baixar\n")

        # Fase 3: Download de poemas faltantes
        logger.info("="*60)
        logger.info("FASE 3: Download de Poemas Faltantes")
        logger.info("="*60)

        download_service = DIContainer.create_download_service(
            Path("arquivos_pessoa"),
            min_delay=2.0,
            max_delay=2.3
        )
        
        async with download_service.http_downloader:
            # Criar rastreador de progresso
            progress_tracker = ProgressTracker(total_faltantes)

            # Baixar poemas faltantes
            for categoria in categorias_faltantes:
                await download_service.download_categoria_recursively(
                    categoria,
                    progress_tracker
                )

        logger.info("\n" + "="*60)
        logger.info("✅ Download de poemas faltantes concluído!")
        logger.info("="*60)
        logger.info(f"📊 Resumo: {progress_tracker.get_summary()}")

    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
