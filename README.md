# Scraper Arquivo Pessoa

Web scraper para extrair poesias do Arquivo Pessoa com Playwright e Beautiful Soup 4 .

## Instalação

### Pré-requisitos

- Python 3.14
- UV (gerenciador de pacotes)

### Passos

```bash
# Clonar ou acessar o diretório
cd scraper_pessoa

# Instalar dependências
uv sync

# Ativar ambiente
source .venv/bin/activate
```

## Arquitetura

O projeto está organizado em 4 camadas + utilidades:

```
Domain Layer
  - Modelos: Poema, Categoria, StructureCatalog
  - Interfaces: IJsonRepository, IPdfFileRepository

Infrastructure Layer
  - PlaywrightBrowser: automação do navegador
  - HttpDownloader: download com retry automático
  - HtmlParserAdapter: parsing de HTML
  - Repositories: persistência em JSON e filesystem

Application Layer
  - WebScraperService: orquestra scraping e extração
  - FilterService: filtra poemas faltantes
  - DownloadService: downloads com delays
  - StructureService: operações sobre estrutura
  - PersistenceService: salvar/carregar catálogo
  - ProgressTracker: rastreia progresso

Utils
  - Logger: logging centralizado
  - Validators: validações de estrutura
  - Helpers: utilitários compartilhados

DIContainer
  - Factory methods para criar serviços
```

## Como Usar

### Scraping Completo (primeira vez)

```bash
python -m src.main_scraper
```

Executa:
1. Acessa a página com Playwright (browser real)
2. Expande categorias via JavaScript
3. Extrai estrutura de categorias e poemas
4. Persiste em output/categorias_estrutura.json
5. Faz download de todos os PDFs com delays

Tempo estimado: 30+ minutos

### Downloads Resumíveis (retomar)

```bash
python -m src.main_download
```

Executa:
1. Carrega estrutura existente do JSON
2. Identifica poemas já baixados
3. Faz download apenas dos faltantes
4. Mostra progresso [N/TOTAL]

## Exemplos de Uso

### Usar DIContainer para criar serviços

```python
from config import DIContainer
import asyncio

async def main():
    # Factory cria serviços com dependências
    scraper = DIContainer.create_scraper_service(headless=True)
    persistence = DIContainer.create_persistence_service()
    
    async with scraper.browser:
        catalog = await scraper.fetch_and_extract_structure()
        await persistence.save_catalog(catalog)

asyncio.run(main())
```

### Filtrar e contar poemas faltantes

```python
from config import DIContainer
import asyncio

async def main():
    persistence = DIContainer.create_persistence_service()
    filter_svc = DIContainer.create_filter_service()
    
    catalog = await persistence.load_catalog()
    
    total_missing = 0
    for categoria in catalog.categorias:
        total_missing += filter_svc.count_missing_poemas(categoria)
    
    print(f"Faltam {total_missing} poemas")

asyncio.run(main())
```

### Usar serviços diretamente

```python
from src.application.filter_service import FilterService
from src.utils.helpers import CategoryHelper

filter_svc = FilterService()

# Filtrar categoria
filtered = filter_svc.filter_missing_poemas(categoria)

# Operações em árvore
depth = CategoryHelper.get_depth(categoria)
flattened = CategoryHelper.flatten_categories(categoria)
CategoryHelper.print_tree(categoria)
```

## Estrutura de Diretórios

```
scraper_pessoa/
├── src/
│   ├── domain/
│   │   ├── models.py
│   │   └── repositories.py
│   ├── infrastructure/
│   │   ├── browser.py
│   │   ├── http_client.py
│   │   ├── parser.py
│   │   └── repositories.py
│   ├── application/
│   │   ├── scraper_service.py
│   │   ├── filter_service.py
│   │   ├── download_service.py
│   │   ├── structure_service.py
│   │   ├── persistence_service.py
│   │   └── progress_tracker.py
│   ├── utils/
│   │   ├── logger.py
│   │   ├── validators.py
│   │   └── helpers.py
│   ├── main_scraper.py
│   └── main_download.py
├── config.py
├── output/
│   └── categorias_estrutura.json
├── arquivos_pessoa/
└── pyproject.toml
```

## Configurações

### Ajustar delays entre downloads

No src/main_download.py, altere:

```python
download_service = DIContainer.create_download_service(
    min_delay=2.0,
    max_delay=2.3
)
```

Aumentar para evitar throttling:
```python
min_delay=5.0,
max_delay=10.0
```

### Headless vs com browser visível

No src/main_scraper.py, altere:

```python
scraper_service = DIContainer.create_scraper_service(headless=False)  # False para ver
```

## Características

- Separação clara em 4 camadas
- Type hints completos
- Context managers para lifecycle management
- Async/await throughout
- Retry automático com backoff exponencial
- Logging centralizado
- Injeção de dependências
- Interfaces abstratas para fácil testes
- Suporte a categorias aninhadas recursivamente
- Progress tracking formatado [N/TOTAL]

## Troubleshooting

### Erro "Módulo src não encontrado"

Execute da raiz do projeto:
```bash
cd /home/maxsonalmeida/Documentos/scraper_pessoa
python -m src.main_scraper
```

### Arquivo categorias_estrutura.json não encontrado

Execute main_scraper.py primeiro:
```bash
python -m src.main_scraper
python -m src.main_download
```

### Timeout no browser

Aumente o timeout em PlaywrightBrowser:
```python
browser = DIContainer.create_scraper_service(headless=True)
# Interno no arquivo browser.py ajustar timeout=60000
```

### Downloads lentos ou falhando

Aumente os delays:
```python
DIContainer.create_download_service(min_delay=5.0, max_delay=15.0)
```
