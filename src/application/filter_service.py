"""Application Filter Service - Filtragem de Arquivos Faltantes"""

import logging
from pathlib import Path
from typing import Optional
from src.domain.models import Categoria

logger = logging.getLogger(__name__)


class FilterService:
    """Serviço para filtrar poemas com arquivos faltantes"""

    def __init__(self, base_path: Path):
        self.base_path = base_path or Path("arquivos_pessoa")

    def filter_missing_poemas(self, categoria: Categoria) -> Optional[Categoria]:
        """
        Filtra categoria deixando apenas poemas sem arquivo baixado.
        Processa recursivamente subcategorias.
        
        Args:
            categoria: Categoria a filtrar
            
        Returns:
            Categoria com apenas poemas faltantes, ou None se nenhum falta
        """
        # Filtra poemas faltantes
        poemas_faltantes = []
        for poema in categoria.poemas:
            pdf_filename = f"{poema.id:04d} - {poema.titulo}.pdf"
            pdf_path = self.base_path / categoria.path / pdf_filename

            if not pdf_path.exists():
                poemas_faltantes.append(poema)

        # Filtra subcategorias recursivamente
        subcategorias_filtradas = []
        for subcategoria in categoria.subcategorias:
            subcat_filtrada = self.filter_missing_poemas(subcategoria)
            if subcat_filtrada:
                subcategorias_filtradas.append(subcat_filtrada)

        # Retorna apenas se houver faltantes
        if poemas_faltantes or subcategorias_filtradas:
            return Categoria(
                nome=categoria.nome,
                path=categoria.path,
                poemas=poemas_faltantes,
                subcategorias=subcategorias_filtradas
            )

        return None

    def count_missing_poemas(self, categoria: Categoria) -> int:
        """
        Conta recursivamente poemas faltantes em uma categoria.
        
        Args:
            categoria: Categoria a contar
            
        Returns:
            Número total de poemas faltantes
        """
        # Contar poemas faltantes nesta categoria
        count = 0
        for poema in categoria.poemas:
            pdf_filename = f"{poema.id:04d} - {poema.titulo}.pdf"
            pdf_path = self.base_path / categoria.path / pdf_filename

            if not pdf_path.exists():
                count += 1

        # Contar recursivamente em subcategorias
        for subcategoria in categoria.subcategorias:
            count += self.count_missing_poemas(subcategoria)

        return count
