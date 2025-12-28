"""Utils Helpers - Funções Auxiliares Utilitárias"""

import logging
from pathlib import Path
from typing import List
from src.domain.models import Categoria

logger = logging.getLogger(__name__)


class PathHelper:
    """Helper para operações com caminhos"""

    @staticmethod
    def ensure_dir(path: Path) -> Path:
        """
        Garante que diretório existe.
        
        Args:
            path: Caminho do diretório
            
        Returns:
            Caminho do diretório criado/existente
        """
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def ensure_parent(path: Path) -> Path:
        """
        Garante que diretório pai existe.
        
        Args:
            path: Caminho do arquivo
            
        Returns:
            Caminho do arquivo
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


class CategoryHelper:
    """Helper para operações com categorias"""

    @staticmethod
    def flatten_categories(categoria: Categoria) -> List[Categoria]:
        """
        Flattena árvore de categorias.
        
        Args:
            categoria: Categoria raiz
            
        Returns:
            Lista de todas as categorias em ordem de profundidade
        """
        result = [categoria]
        for subcat in categoria.subcategorias:
            result.extend(CategoryHelper.flatten_categories(subcat))
        return result

    @staticmethod
    def get_depth(categoria: Categoria) -> int:
        """
        Calcula profundidade máxima da categoria.
        
        Args:
            categoria: Categoria a medir
            
        Returns:
            Profundidade (0 se sem subcategorias)
        """
        if not categoria.subcategorias:
            return 0

        max_depth = 0
        for subcat in categoria.subcategorias:
            depth = 1 + CategoryHelper.get_depth(subcat)
            max_depth = max(max_depth, depth)

        return max_depth

    @staticmethod
    def print_tree(categoria: Categoria, indent: int = 0) -> None:
        """
        Imprime árvore de categorias.
        
        Args:
            categoria: Categoria a imprimir
            indent: Nível de indentação
        """
        prefix = "  " * indent
        poema_count = len(categoria.poemas)
        sub_count = len(categoria.subcategorias)

        logger.info(f"{prefix}📁 {categoria.nome} ({poema_count} poemas, {sub_count} subcategorias)")

        for poema in categoria.poemas:
            logger.info(f"{prefix}  📄 [{poema.id}] {poema.titulo}")

        for subcat in categoria.subcategorias:
            CategoryHelper.print_tree(subcat, indent + 1)


class TextHelper:
    """Helper para operações com texto"""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitiza nome de arquivo.
        
        Args:
            filename: Nome a sanitizar
            
        Returns:
            Nome sanitizado
        """
        # Remover caracteres inválidos para nomes de arquivo
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()

    @staticmethod
    def truncate(text: str, max_length: int = 50) -> str:
        """
        Trunca texto com reticências.
        
        Args:
            text: Texto a truncar
            max_length: Comprimento máximo
            
        Returns:
            Texto truncado
        """
        if len(text) > max_length:
            return text[:max_length - 3] + "..."
        return text
