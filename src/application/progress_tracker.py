"""Application Progress Tracker - Rastreamento de Progresso"""

import logging
from typing import Callable

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Rastreador de progresso de downloads"""

    def __init__(self, total: int):
        self.total = total
        self.atual = 0
        self.callbacks: list[Callable] = []

    def increment(self, title: str = "") -> None:
        """
        Incrementa contador e notifica.
        
        Args:
            title: Descrição opcional do item incrementado
        """
        self.atual += 1
        progress_str = f"[{self.atual:04d}/{self.total:04d}]"
        if title:
            logger.info(f"  ✓ {progress_str} {title}")
        else:
            logger.info(f"  ✓ {progress_str}")

        # Executar callbacks registrados
        for callback in self.callbacks:
            callback(self.atual, self.total)

    def on_progress(self, callback: Callable[[int, int], None]) -> None:
        """
        Registra callback para ser chamado ao incrementar.
        
        Args:
            callback: Função(atual, total)
        """
        self.callbacks.append(callback)

    @property
    def progress_percent(self) -> float:
        """Retorna percentual de progresso"""
        if self.total == 0:
            return 0
        return (self.atual / self.total) * 100

    def get_summary(self) -> str:
        """Retorna resumo do progresso"""
        return f"{self.atual}/{self.total} ({self.progress_percent:.1f}%)"
