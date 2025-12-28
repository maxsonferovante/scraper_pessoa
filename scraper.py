import asyncio
import httpx
import logging
import random
from retry import retry
from pathlib import Path
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import Optional
from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Poema(BaseModel):
    """Modelo para representar um poema"""
    id: int
    titulo: str
    categoria_path: str


class Categoria(BaseModel):
    """Modelo para representar uma categoria"""
    nome: str
    path: str
    poemas: list[Poema] = []
    subcategorias: list['Categoria'] = []


Categoria.model_rebuild()


class ArquivoPessoaScraper:
    """Scraper para arquivopessoa.net com suporte a AJAX/JavaScript"""
    
    BASE_URL = "http://arquivopessoa.net"
    PDF_URL_TEMPLATE = f"{BASE_URL}/typographia/textos/arquivopessoa-{{}}.pdf"
    OUTPUT_DIR = Path("arquivos_pessoa")
    
    def __init__(self, is_headless: bool = True):
        self.browser = None
        self.page = None
        self.http_client: httpx.AsyncClient = None
        self.playwright = None
        self.is_headless = is_headless
    
    async def __aenter__(self):
        # Inicia Playwright
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.is_headless, devtools=True)  # headless=True para velocidade
        self.page = await self.browser.new_page()
        
        # Cliente HTTP para downloads
        self.http_client = httpx.AsyncClient(timeout=30.0, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/pdf",
            "Accept-Language": "pt-BR,pt;q=0.9",
            "Referer": self.BASE_URL,
            "Connection": "keep-alive",
        })
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        if self.http_client:
            await self.http_client.aclose()
    
    async def fetch_page_with_js(self) -> str:
        """Acessa a página principal e executa todo o JavaScript"""
        try:
            logger.info("🌐 Carregando página com Playwright...")
            await self.page.goto(self.BASE_URL, wait_until='networkidle')
            
            logger.info("⏳ Expandindo categorias dinamicamente...")
            await self._expand_all_categories()
            
            # Aguarda bastante tempo para garantir que todo AJAX foi processado
            logger.info("⏰ Aguardando processamento final de AJAX...")
            await self.page.wait_for_timeout(3000)
            
            html = await self.page.content()
            logger.info("✓ Página carregada com todo o conteúdo dinâmico")
            return html
        except Exception as e:
            logger.error(f"Erro ao carregar página com Playwright: {e}")
            raise
    
    async def _expand_all_categories(self):
        """
        Executa JavaScript para simular cliques em TODOS os botões .ctrl-opener.
        """
        logger.info("  Injetando JavaScript para expandir todas as categorias...")
        
        # JavaScript que clica em todos os .ctrl-opener sequencialmente
        expand_script = """
        (async function() {
            let attempts = 0;
            const maxAttempts = 500;  // Balanço entre speed e cobertura
            const clickedOpeners = new Set();

            while (attempts < maxAttempts) {
                const openers = document.querySelectorAll('a.ctrl-opener');
                if (openers.length === 0) {
                    console.log('Todos os openers foram clicados.');
                    break;
                }
                

                //clicar em todos os openers um por um com delay
                for (const opener of openers) {
                    if (clickedOpeners.has(opener)) {
                        continue;  // Já clicado
                    }
                    clickedOpeners.add(opener);
                    opener.click();
                    await new Promise(r => setTimeout(r, 450));  // Pequena pausa entre cliques
                }

                attempts++;
                console.log(`Iteração ${attempts} completa. Restam ${openers.length} openers.`);
                
            }
            console.log(`Cliquei em todos os openers em ${attempts} iterações. Total clics: ${clickedOpeners.size}`);
            
            return `Expandido em ${attempts} iterações`;
        })()
        """
        
        try:
            result = await self.page.evaluate(expand_script)
            logger.info(f"  ✓ {result}")
        except Exception as e:
            logger.error(f"  ❌ Erro ao executar JavaScript: {e}")
            raise
    
    def extract_categories(self, html: str) -> list[Categoria]:
        """Extrai categorias principais do HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        categorias = []
        
        ul_indice = soup.find('ul', class_='indice')
        if not ul_indice:
            logger.warning("Nenhuma lista de índice encontrada")
            return categorias
        
        # Pega categorias principais (primeiro nível)
        for li_categoria in ul_indice.find_all('li', class_='categoria', recursive=False):
            categoria = self._parse_categoria(li_categoria)
            if categoria:
                categorias.append(categoria)
        
        return categorias
    
    def _parse_categoria(self, li_element, parent_path: str = "") -> Optional[Categoria]:
        """Parse de uma categoria individual"""
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
            
            # Procura por poemas dentro desta categoria
            ul_interna = li_element.find('ul', recursive=False)
            if ul_interna:
                # Procura por poemas diretos
                for li_texto in ul_interna.find_all('li', class_='texto', recursive=False):
                    poema = self._parse_poema(li_texto, path)
                    if poema:
                        categoria.poemas.append(poema)
                
                # Procura por subcategorias
                for li_sub in ul_interna.find_all('li', class_='categoria', recursive=False):
                    sub_categoria = self._parse_categoria(li_sub, path)
                    if sub_categoria:
                        categoria.subcategorias.append(sub_categoria)
            
            return categoria
        except Exception as e:
            logger.error(f"Erro ao fazer parse da categoria: {e}")
            return None
    
    def _parse_poema(self, li_element, categoria_path: str) -> Optional[Poema]:
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
                return Poema(id=poema_id, titulo=titulo, categoria_path=categoria_path)
        except Exception as e:
            logger.error(f"Erro ao fazer parse do poema: {e}")
            return None
    
    @retry(tries=3, delay=2, backoff=2, logger=logger, exceptions=(httpx.HTTPError, httpx.ReadTimeout, Exception))
    async def download_pdf(self, poema_id: int, save_path: Path):
        """Faz download de um PDF do poema"""
        url = self.PDF_URL_TEMPLATE.format(poema_id)
        
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Baixando PDF: {poema_id} → {save_path.name}")
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            save_path.write_bytes(response.content)
            logger.info(f"✓ Salvo: {save_path.name}")
        except httpx.HTTPError as e:
            logger.error(f"Erro ao baixar PDF {poema_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao baixar PDF {poema_id}: {e}")
            raise
    
    async def download_all_poemas(self, categoria: Categoria, base_path: Optional[Path] = None):
        """Baixa todos os poemas de uma categoria recursivamente"""
        if base_path is None:
            base_path = self.OUTPUT_DIR
        
        # Cria a pasta da categoria
        categoria_dir = base_path / categoria.path
        categoria_dir.mkdir(parents=True, exist_ok=True)
        
        # Baixa poemas da categoria atual
        for poema in categoria.poemas:
            pdf_filename = f"{poema.id:04d} - {poema.titulo}.pdf"
            pdf_path = categoria_dir / pdf_filename
            await self.download_pdf(poema.id, pdf_path)            
            # Pequena pausa aleatória entre downloads para evitar sobrecarga
            pause_duration = random.uniform(3,7)
            logger.info(f"Pausando por {pause_duration:.2f} segundos para evitar sobrecarga...")
            await asyncio.sleep(pause_duration)
        
        # Processa subcategorias
        for subcategoria in categoria.subcategorias:
            await self.download_all_poemas(subcategoria, base_path)
    
    def print_structure(self, categoria: Categoria, indent: int = 0):
        """Imprime a estrutura de categorias e poemas"""
        prefix = "  " * indent
        logger.info(f"{prefix}📁 {categoria.nome}")
        
        for poema in categoria.poemas:
            logger.info(f"{prefix}  📄 [{poema.id}] {poema.titulo}")
        
        for sub in categoria.subcategorias:
            self.print_structure(sub, indent + 1)
    


    def _count_poemas(self, categoria: Categoria) -> int:
        """Conta poemas recursivamente"""
        count = len(categoria.poemas)
        for sub in categoria.subcategorias:
            count += self._count_poemas(sub)
        return count

def save_to_file_json(data: dict, filepath: Path):
    """Salva dados em um arquivo JSON"""
    import json
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logger.info(f"✓ Dados salvos em {filepath}")


async def main():
    logger.info("🚀 Iniciando scraper do Arquivo Pessoa")
    
    try:
        async with ArquivoPessoaScraper(is_headless=False) as scraper:
            # Step 1: Fetch página principal com JavaScript
            logger.info("\n[1] Acessando página principal e expandindo categorias...")
            html = await scraper.fetch_page_with_js()
            
            # Step 2: Extract categorias
            logger.info("\n[2] Extraindo categorias do HTML...")
            categorias = scraper.extract_categories(html)
            logger.info(f"✓ {len(categorias)} categorias principais encontradas")
            
            # Step 3: Print structure
            logger.info("\n[3] Estrutura de categorias e poemas:")
            total_poemas = 0
            for cat in categorias:
                # scraper.print_structure(cat)
                total_poemas += scraper._count_poemas(cat)
            
            logger.info(f"\n📊 Total: {total_poemas} poemas a baixar")
            
            data = {
                "total_categorias": len(categorias),
                "total_poemas": total_poemas,
                "categorias": [cat.model_dump() for cat in categorias]
            }
            save_to_file_json(
                data=data,
                filepath=Path("output/categorias_estrutura.json")
            )
            # Step 4: Download PDFs
            logger.info("\n[4] Iniciando download dos PDFs...")
            for categoria in categorias:
                await scraper.download_all_poemas(categoria)
            
            logger.info("\n✅ Scraper concluído!")
    
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
