import asyncio
import os
import json
import random
import logging
from pathlib import Path
from pydantic import BaseModel
from scraper import ArquivoPessoaScraper  

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



# vamos ler o diretorio arquivo_pessoa, carregar as categorias e os poemas nas estruturas de  dados, e baixar os poemas que ainda nao foram baixados
# usaremos o ArquivoPessoaScraper para baixar apenas usando o metodo download_pdf
# a logica de carregar as categorias e poemas não existe
# nem a logica de comparação com o que tem em outpout/categorias_estrutura.json que tem todos as categorias e poemas ja baixados
# o script deve baixar os poemas que ainda não foram baixados, ou seja, que não existem em output/poemas/{categoria_slug}/{poema_slug}.pdf

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

def load_existing_structure_recursively(data) -> Categoria:
    """Carrega a estrutura de categorias e poemas recursivamente a partir de um dicionário"""
    categoria = Categoria(
        nome=data['nome'],
        path=data['path'],
        poemas=[Poema(**poema) for poema in data.get('poemas', [])],
        subcategorias=[load_existing_structure_recursively(subcat) for subcat in data.get('subcategorias', [])]
    )
    return categoria



def filter_categorias_and_poemas_missing_files(categoria: Categoria) -> Categoria | None:
    """Filtra categorias e poemas que não possuem arquivos PDF baixados"""
    base_path = Path("arquivos_pessoa")
    
    # Filtra poemas que ainda não foram baixados
    poemas_faltantes = []
    for poema in categoria.poemas:
        pdf_filename = f"{poema.id:04d} - {poema.titulo}.pdf"
        pdf_path = base_path / categoria.path / pdf_filename
        
        if not pdf_path.exists():
            poemas_faltantes.append(poema)
            logger.info(f"  Poema faltante: {pdf_filename}")
    
    # Filtra subcategorias recursivamente
    subcategorias_filtradas = []
    for subcategoria in categoria.subcategorias:
        subcat_filtrada = filter_categorias_and_poemas_missing_files(subcategoria)
        if subcat_filtrada:
            subcategorias_filtradas.append(subcat_filtrada)
    
    # Retorna a categoria apenas se houver poemas ou subcategorias faltantes
    if poemas_faltantes or subcategorias_filtradas:
        return Categoria(
            nome=categoria.nome,
            path=categoria.path,
            poemas=poemas_faltantes,
            subcategorias=subcategorias_filtradas
        )
    
    return None


def count_missing_poemas(categoria: Categoria) -> int:
    """Conta recursivamente todos os poemas faltantes em uma categoria e suas subcategorias"""
    base_path = Path("arquivos_pessoa")
    
    # Contar poemas faltantes nesta categoria
    count = 0
    for poema in categoria.poemas:
        pdf_filename = f"{poema.id:04d} - {poema.titulo}.pdf"
        pdf_path = base_path / categoria.path / pdf_filename
        
        if not pdf_path.exists():
            count += 1
    
    # Contar recursivamente em subcategorias
    for subcategoria in categoria.subcategorias:
        count += count_missing_poemas(subcategoria)
    
    return count


async def download_categoria_recursively(
    categoria: Categoria,
    scraper: 'ArquivoPessoaScraper',
    base_path: Path,
    contador: dict  # {'atual': int, 'total': int}
):
    """
    Processa recursivamente uma categoria e suas subcategorias,
    baixando todos os poemas faltantes com delays.
    """
    categoria_filtrada = filter_categorias_and_poemas_missing_files(categoria)
    
    if not categoria_filtrada:
        return
    
    # Baixar poemas desta categoria
    if categoria_filtrada.poemas:
        categoria_dir = base_path / categoria_filtrada.path
        categoria_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Baixando {len(categoria_filtrada.poemas)} poemas de '{categoria_filtrada.nome}'...")
        
        for poema in categoria_filtrada.poemas:
            pdf_filename = f"{poema.id:04d} - {poema.titulo}.pdf"
            pdf_path = categoria_dir / pdf_filename
            try:
                await scraper.download_pdf(poema.id, pdf_path)
                contador['atual'] += 1
                logger.info(f"  ✓ [{contador['atual']:04d}/{contador['total']:04d}] {pdf_filename}")
            except Exception as e:
                contador['atual'] += 1
                logger.error(f"  ✗ [{contador['atual']:04d}/{contador['total']:04d}] {pdf_filename}: {e}")
            
            pause_duration = random.uniform(2,2.3)
            logger.info(f"  Pausando por {pause_duration:.2f} segundos...")
            await asyncio.sleep(pause_duration)
    
    # Processar subcategorias recursivamente
    for subcategoria in categoria_filtrada.subcategorias:
        await download_categoria_recursively(subcategoria, scraper, base_path, contador)


async def main():
    async with ArquivoPessoaScraper() as scraper:
        logger.info("Carregando estrutura existente de categorias e poemas...")
        estrutura_path = os.path.join("output", "categorias_estrutura.json")
        if not os.path.exists(estrutura_path):
            logger.error(f"Estrutura de categorias não encontrada em {estrutura_path}")
            return

        with open(estrutura_path, "r", encoding="utf-8") as f:
            categorias_data = json.load(f)

        logger.info("Iniciando download de poemas faltantes...")
        
        # Extrair lista de categorias do JSON (estrutura: {"categorias": [...], ...})
        categorias_lista = categorias_data.get('categorias', [])
        
        if not categorias_lista:
            logger.warning("Nenhuma categoria encontrada no arquivo JSON")
            return
        
        base_path = scraper.OUTPUT_DIR
        logger.info(f"Processando {len(categorias_lista)} categorias principais...")
        
        # Contar todos os poemas faltantes
        total_poemas_faltantes = 0
        for categoria_dict in categorias_lista:
            categoria = load_existing_structure_recursively(categoria_dict)
            total_poemas_faltantes += count_missing_poemas(categoria)
        
        if total_poemas_faltantes == 0:
            logger.info("✅ Nenhum poema faltante encontrado!")
            return
        
        logger.info(f"📊 Total de {total_poemas_faltantes} poemas para baixar\n")
        
        # Inicializar contador
        contador = {'atual': 0, 'total': total_poemas_faltantes}
        
        # Processar cada categoria recursivamente
        for categoria_dict in categorias_lista:
            categoria = load_existing_structure_recursively(categoria_dict)
            await download_categoria_recursively(categoria, scraper, base_path, contador)
        
        logger.info("\n✅ Download de poemas faltantes concluído!")


if __name__ == "__main__":
    asyncio.run(main())
