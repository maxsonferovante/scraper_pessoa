"""Infrastructure Browser - Gerenciamento de Playwright"""

import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)


class PlaywrightBrowser:
    """Gerenciador de browser Playwright com lifecycle management"""

    BASE_URL = "http://arquivopessoa.net"

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def __aenter__(self):
        """Context manager entry - inicia browser"""
        logger.info("🌐 Iniciando Playwright...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            devtools=not self.headless
        )
        self.page = await self.browser.new_page()
        logger.info("✓ Playwright iniciado")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - fecha browser"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("✓ Playwright fechado")

    async def fetch_with_javascript(self) -> str:
        """
        Acessa página principal e executa JavaScript para expandir categorias.
        Retorna o HTML completo com AJAX processado.
        """
        if not self.page:
            raise RuntimeError("Browser não foi inicializado. Use com context manager.")

        try:
            logger.info("🌐 Navegando para página principal...")
            await self.page.goto(self.BASE_URL, wait_until='networkidle')

            logger.info("⏳ Executando JavaScript para expandir categorias...")
            await self._expand_all_categories()

            logger.info("⏰ Aguardando processamento final de AJAX...")
            await self.page.wait_for_timeout(3000)

            html = await self.page.content()
            logger.info("✓ Página carregada com conteúdo dinâmico")
            return html

        except Exception as e:
            logger.error(f"❌ Erro ao carregar página: {e}")
            raise

    async def _expand_all_categories(self) -> None:
        """Injeta JavaScript para expandir todas as categorias dinamicamente"""
        if not self.page:
            raise RuntimeError("Page não inicializada")

        expand_script = """
        (async function() {
            let attempts = 0;
            const maxAttempts = 500;
            const clickedOpeners = new Set();

            while (attempts < maxAttempts) {
                const openers = document.querySelectorAll('a.ctrl-opener');
                if (openers.length === 0) {
                    console.log('Todas as categorias foram expandidas.');
                    break;
                }

                for (const opener of openers) {
                    if (clickedOpeners.has(opener)) {
                        continue;
                    }
                    clickedOpeners.add(opener);
                    opener.click();
                    await new Promise(r => setTimeout(r, 450));
                }

                attempts++;
                console.log(`Iteração ${attempts} completa. Total clicks: ${clickedOpeners.size}`);
            }

            return `Categorias expandidas em ${attempts} iterações (${clickedOpeners.size} cliques)`;
        })()
        """

        try:
            result = await self.page.evaluate(expand_script)
            logger.info(f"  ✓ {result}")
        except Exception as e:
            logger.error(f"  ❌ Erro ao executar JavaScript: {e}")
            raise
