"""Application Persistence Service - Coordenação de Persistência"""

import logging
from pathlib import Path
from src.domain.models import StructureCatalog
from src.domain.repositories import IJsonRepository
from src.application.structure_service import StructureService

logger = logging.getLogger(__name__)


class PersistenceService:
    """Serviço de persistência e recuperação de estrutura"""

    def __init__(self, json_repository: IJsonRepository):
        self.structure_service = StructureService(json_repository)

    async def save_catalog(
        self,
        catalog: StructureCatalog,
        filepath: Path
    ) -> Path:
        """
        Salva catálogo em arquivo.
        
        Args:
            catalog: Catálogo a salvar
            filepath: Caminho (default: output/categorias_estrutura.json)
            
        Returns:
            Caminho do arquivo salvo
        """
        if filepath is None:
            filepath = Path("output/categorias_estrutura.json")

        await self.structure_service.save_structure(catalog, filepath)
        return filepath

    async def load_catalog(self) -> StructureCatalog:
        """
        Carrega catálogo de arquivo.
        
        Args:
            filepath: Caminho (default: output/categorias_estrutura.json)
            
        Returns:
            Catálogo carregado
        """
        filepath = Path("output/categorias_estrutura.json")

        if not filepath.exists():
            raise FileNotFoundError(f"Arquivo de estrutura não encontrado: {filepath}")

        return await self.structure_service.load_structure(filepath)
