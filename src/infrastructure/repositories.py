"""Infrastructure Repositories - Implementações Concretas"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
from src.domain.repositories import IJsonRepository, IPdfFileRepository
from src.domain.models import StructureCatalog

logger = logging.getLogger(__name__)


class JsonStructureRepository(IJsonRepository):
    """Repositório para persistência de estrutura em JSON"""

    async def save(self, data: StructureCatalog, filepath: Path) -> None:
        """
        Salva catálogo em arquivo JSON.
        
        Args:
            data: Catálogo a ser salvo
            filepath: Caminho do arquivo JSON
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with filepath.open('w', encoding='utf-8') as f:
            json.dump(data.model_dump(), f, ensure_ascii=False, indent=4)

        logger.info(f"✓ Estrutura salva em {filepath}")

    async def load(self, filepath: Path) -> Dict[str, Any]:
        """
        Carrega estrutura de arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo JSON
            
        Returns:
            Dicionário com a estrutura carregada
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

        with filepath.open('r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"✓ Estrutura carregada de {filepath}")
        return data


class PdfFileRepository(IPdfFileRepository):
    """Repositório para gerenciamento de arquivos PDF no sistema de arquivos"""

    def __init__(self, base_path: Path):
        self.base_path = base_path or Path("arquivos_pessoa")

    async def exists(self, filepath: Path) -> bool:
        """Verifica se arquivo PDF existe"""
        return filepath.exists()

    async def save(self, content: bytes, filepath: Path) -> None:
        """
        Salva conteúdo PDF em arquivo.
        
        Args:
            content: Conteúdo do PDF em bytes
            filepath: Caminho onde salvar
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_bytes(content)
        logger.debug(f"PDF salvo: {filepath}")

    async def get_size(self, filepath: Path) -> int:
        """Obtém tamanho do arquivo em bytes"""
        if not filepath.exists():
            return 0
        return filepath.stat().st_size

    async def delete(self, filepath: Path) -> None:
        """Deleta arquivo PDF"""
        if filepath.exists():
            filepath.unlink()
            logger.debug(f"PDF deletado: {filepath}")
