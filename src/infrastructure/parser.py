"""Infrastructure Parser - Abstração sobre BeautifulSoup"""

import logging
from typing import Optional, List
from bs4 import BeautifulSoup
from src.domain.models import Categoria, Poema

logger = logging.getLogger(__name__)


class HtmlParserAdapter:
    """Adaptador para parsing de HTML com BeautifulSoup"""

    def parse_categories(self, html: str) -> List[Categoria]:
        """
        Extrai categorias principais do HTML.
        
        Args:
            html: Conteúdo HTML da página
            
        Returns:
            Lista de categorias de primeiro nível
        """
        soup = BeautifulSoup(html, 'html.parser')
        categorias = []

        ul_indice = soup.find('ul', class_='indice')
        if not ul_indice:
            logger.warning("Nenhuma lista de índice encontrada")
            return categorias

        # Extrai categorias principais (primeiro nível)
        for li_categoria in ul_indice.find_all('li', class_='categoria', recursive=False):
            categoria = self._parse_categoria(li_categoria)
            if categoria:
                categorias.append(categoria)

        return categorias

    def _parse_categoria(
        self,
        li_element,
        parent_path: str = ""
    ) -> Optional[Categoria]:
        """Parse de uma categoria individual (recursiva)"""
        try:
            # Extrai o nome da categoria
            span = li_element.find('span', class_='titulo-categoria')
            if not span:
                return None

            titulo = span.get_text(strip=True)

            # Cria o caminho da pasta
            if parent_path:
                path = f"{parent_path}/{titulo}"
            else:
                path = titulo

            categoria = Categoria(nome=titulo, path=path)

            # Procura por poemas e subcategorias
            ul_interna = li_element.find('ul', recursive=False)
            if ul_interna:
                # Poemas diretos
                for li_texto in ul_interna.find_all('li', class_='texto', recursive=False):
                    poema = self._parse_poema(li_texto, path)
                    if poema:
                        categoria.poemas.append(poema)

                # Subcategorias
                for li_sub in ul_interna.find_all('li', class_='categoria', recursive=False):
                    sub_categoria = self._parse_categoria(li_sub, path)
                    if sub_categoria:
                        categoria.subcategorias.append(sub_categoria)

            return categoria
        except Exception as e:
            logger.error(f"Erro ao fazer parse da categoria: {e}")
            return None

    def _parse_poema(
        self,
        li_element,
        categoria_path: str
    ) -> Optional[Poema]:
        """Parse de um poema individual"""
        try:
            a_tag = li_element.find('a', class_='titulo-texto')
            if not a_tag:
                return None

            href = a_tag.get('href', '')
            titulo = a_tag.get_text(strip=True)

            # Extrai o ID do poema da URL (/textos/[ID])
            if '/textos/' in href:
                poema_id = int(href.split('/textos/')[-1])
                return Poema(
                    id=poema_id,
                    titulo=titulo,
                    categoria_path=categoria_path
                )
        except Exception as e:
            logger.error(f"Erro ao fazer parse do poema: {e}")
            return None
