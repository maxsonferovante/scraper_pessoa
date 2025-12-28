"""Domain Repositories - Interfaces Abstratas"""

from abc import ABC, abstractmethod
from pathlib import Path
from src.domain.models import StructureCatalog


class IJsonRepository(ABC):
    """Interface para persistência de estrutura em JSON"""

    @abstractmethod
    async def save(self, data: StructureCatalog, filepath: Path) -> None:
        """Salva catálogo em arquivo JSON"""
        pass

    @abstractmethod
    async def load(self, filepath: Path) -> dict:
        """Carrega estrutura de arquivo JSON"""
        pass


class IPdfFileRepository(ABC):
    """Interface para gerenciamento de arquivos PDF"""

    @abstractmethod
    async def exists(self, filepath: Path) -> bool:
        """Verifica se arquivo PDF existe"""
        pass

    @abstractmethod
    async def save(self, content: bytes, filepath: Path) -> None:
        """Salva conteúdo PDF em arquivo"""
        pass

    @abstractmethod
    async def get_size(self, filepath: Path) -> int:
        """Obtém tamanho do arquivo em bytes"""
        pass


class IDownloadRepository(ABC):
    """Interface para fazer download de PDFs"""

    @abstractmethod
    async def download_pdf(self, poema_id: int, save_path: Path) -> None:
        """Faz download de um PDF específico"""
        pass
