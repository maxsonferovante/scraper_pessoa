"""Application Structure Service - Operações sobre Estrutura de Categorias"""

import logging
from pathlib import Path
from typing import List
from src.domain.models import Categoria, StructureCatalog
from src.domain.repositories import IJsonRepository

logger = logging.getLogger(__name__)


class StructureService:
    """Serviço para operações sobre estrutura de categorias"""

    def __init__(self, json_repository: IJsonRepository):
        self.json_repository = json_repository

    async def save_structure(
        self,
        catalog: StructureCatalog,
        filepath: Path
    ) -> None:
        """
        Persiste catálogo em arquivo JSON.
        
        Args:
            catalog: Catálogo a persistir
            filepath: Caminho do arquivo JSON
        """
        await self.json_repository.save(catalog, filepath)
        logger.info(f"✓ {catalog.total_categorias} categorias e {catalog.total_poemas} poemas salvos")

    async def load_structure(self, filepath: Path) -> StructureCatalog:
        """
        Carrega catálogo de arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo JSON
            
        Returns:
            Catálogo carregado
        """
        data = await self.json_repository.load(filepath)
        
        # Reconstruir objetos Categoria a partir do dicionário
        categorias = self._load_categorias_from_dict(data.get('categorias', []))
        
        catalog = StructureCatalog(
            total_categorias=data.get('total_categorias', 0),
            total_poemas=data.get('total_poemas', 0),
            categorias=categorias
        )
        logger.info(f"✓ {catalog.total_categorias} categorias carregadas")
        return catalog

    @staticmethod
    def _load_categorias_from_dict(data_list: List[dict]) -> List[Categoria]:
        """Reconstrói objetos Categoria a partir de dicionários"""
        categorias = []
        for cat_dict in data_list:
            categoria = Categoria(
                nome=cat_dict['nome'],
                path=cat_dict['path'],
                poemas=[],  # Será preenchido abaixo
                subcategorias=[]
            )
            
            # Adicionar poemas
            for poema_dict in cat_dict.get('poemas', []):
                from src.domain.models import Poema
                categoria.poemas.append(Poema(**poema_dict))
            
            # Adicionar subcategorias recursivamente
            if cat_dict.get('subcategorias'):
                categoria.subcategorias = StructureService._load_categorias_from_dict(
                    cat_dict['subcategorias']
                )
            
            categorias.append(categoria)
        
        return categorias

    @staticmethod
    def count_poemas_recursively(categoria: Categoria) -> int:
        """Conta poemas recursivamente em uma categoria e subcategorias"""
        count = len(categoria.poemas)
        for sub in categoria.subcategorias:
            count += StructureService.count_poemas_recursively(sub)
        return count

    @staticmethod
    def count_categorias_recursively(categoria: Categoria) -> int:
        """Conta categorias recursivamente"""
        count = 1  # A própria categoria
        for sub in categoria.subcategorias:
            count += StructureService.count_categorias_recursively(sub)
        return count
