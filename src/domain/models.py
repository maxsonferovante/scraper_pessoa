"""Domain Models - Entidades do Negócio"""

from pydantic import BaseModel, Field
from typing import List

class Poema(BaseModel):
    """Modelo que representa um poema"""
    id: int
    titulo: str
    categoria_path: str

    class Config:
        frozen = True  # Imutável


class Categoria(BaseModel):
    """Modelo que representa uma categoria com estrutura recursiva"""
    nome: str
    path: str
    poemas: List[Poema] = Field(default_factory=list)
    subcategorias: List['Categoria'] = Field(default_factory=list)

    class Config:
        frozen = False


# Rebuild forward references
Categoria.model_rebuild()


class PdfMetadata(BaseModel):
    """Metadados de um PDF para download"""
    poema_id: int
    titulo: str
    categoria_path: str
    filename: str = Field(default="")

    def __init__(self, **data):
        super().__init__(**data)
        if not self.filename:
            object.__setattr__(self, 'filename', f"{self.poema_id:04d} - {self.titulo}.pdf")

    class Config:
        frozen = True


class StructureCatalog(BaseModel):
    """Catálogo de estrutura completo"""
    total_categorias: int
    total_poemas: int
    categorias: List[Categoria]

    @classmethod
    def from_categorias(cls, categorias: List[Categoria]) -> 'StructureCatalog':
        """Factory method para criar catálogo a partir de lista de categorias"""
        total_poemas = sum(_count_poemas(cat) for cat in categorias)
        return cls(
            total_categorias=len(categorias),
            total_poemas=total_poemas,
            categorias=categorias
        )


def _count_poemas(categoria: Categoria) -> int:
    """Função auxiliar para contar poemas recursivamente"""
    count = len(categoria.poemas)
    for sub in categoria.subcategorias:
        count += _count_poemas(sub)
    return count
