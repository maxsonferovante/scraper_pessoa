"""Utils Validators - Validações de Estrutura e Dados"""

import logging
from typing import Optional
from pathlib import Path
from src.domain.models import Categoria, Poema, StructureCatalog

logger = logging.getLogger(__name__)


class StructureValidator:
    """Validador de integridade da estrutura de categorias"""

    @staticmethod
    def validate_categoria(categoria: Categoria) -> bool:
        """
        Valida se uma categoria está bem formada.
        
        Args:
            categoria: Categoria a validar
            
        Returns:
            True se válida, False caso contrário
        """
        if not categoria.nome or not isinstance(categoria.nome, str):
            logger.warning(f"Categoria com nome inválido: {categoria.nome}")
            return False

        if not categoria.path or not isinstance(categoria.path, str):
            logger.warning(f"Categoria com path inválido: {categoria.path}")
            return False

        # Validar poemas
        for poema in categoria.poemas:
            if not StructureValidator.validate_poema(poema):
                return False

        # Validar subcategorias recursivamente
        for subcat in categoria.subcategorias:
            if not StructureValidator.validate_categoria(subcat):
                return False

        return True

    @staticmethod
    def validate_poema(poema: Poema) -> bool:
        """
        Valida se um poema está bem formado.
        
        Args:
            poema: Poema a validar
            
        Returns:
            True se válido, False caso contrário
        """
        if not isinstance(poema.id, int) or poema.id <= 0:
            logger.warning(f"Poema com ID inválido: {poema.id}")
            return False

        if not poema.titulo or not isinstance(poema.titulo, str):
            logger.warning(f"Poema com título inválido: {poema.titulo}")
            return False

        if not poema.categoria_path or not isinstance(poema.categoria_path, str):
            logger.warning(f"Poema com categoria_path inválido: {poema.categoria_path}")
            return False

        return True

    @staticmethod
    def validate_catalog(catalog: StructureCatalog) -> bool:
        """
        Valida integridade completa do catálogo.
        
        Args:
            catalog: Catálogo a validar
            
        Returns:
            True se válido, False caso contrário
        """
        if catalog.total_categorias < 0 or catalog.total_poemas < 0:
            logger.warning("Catálogo com totais negativos")
            return False

        if not catalog.categorias:
            logger.warning("Catálogo com lista de categorias vazia")
            return False

        # Validar cada categoria
        for categoria in catalog.categorias:
            if not StructureValidator.validate_categoria(categoria):
                return False

        return True


class FileValidator:
    """Validador de operações de arquivo"""

    @staticmethod
    def validate_pdf_path(filepath: Path) -> bool:
        """
        Valida se caminho de PDF é válido.
        
        Args:
            filepath: Caminho do arquivo
            
        Returns:
            True se válido
        """
        if not filepath.name.endswith('.pdf'):
            logger.warning(f"Arquivo não é PDF: {filepath}")
            return False

        return True

    @staticmethod
    def validate_json_path(filepath: Path) -> bool:
        """
        Valida se caminho de JSON é válido.
        
        Args:
            filepath: Caminho do arquivo
            
        Returns:
            True se válido
        """
        if not filepath.name.endswith('.json'):
            logger.warning(f"Arquivo não é JSON: {filepath}")
            return False

        return True
