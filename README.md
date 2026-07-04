# QuintoAndar - Condomínios de Florianópolis

Este repositório contém o mapeamento e extração completa de todos os condomínios de Florianópolis cadastrados na plataforma QuintoAndar. O projeto foi projetado com uma estrutura organizada de scripts e dados prontos para importação (XML/CSV) e clonagem de páginas de condomínios.

## Estrutura do Projeto

```text
quintoandar_florianopolis_condos/
├── README.md                  # Este guia do projeto
├── data/                      # Arquivos de dados extraídos
│   ├── florianopolis_condos.xml          # XML estruturado com fotos, descrição, specs e mapa
│   ├── florianopolis_condos_detailed.csv # CSV com nome, endereço, bairro e coordenadas
│   └── florianopolis_condos.txt          # Lista bruta das URLs dos condomínios
├── scripts/                   # Scripts de automação em Python
│   ├── extract_condos.py      # Passo 1: Extrai as URLs a partir dos sitemaps
│   ├── scrape_all_condos.py   # Passo 2: Mapeia dados básicos para CSV
│   ├── scrape_to_xml.py       # Passo 3: Mapeia dados completos para XML
│   ├── download_images.py     # Utilitário: Baixa as fotos locais de forma controlada
│   └── remove_watermarks.py   # Utilitário: Limpa marcas d'água das fotos via OpenCV
└── images/                    # Pasta gerada dinamicamente ao baixar fotos
```

---

## Estrutura do XML (`florianopolis_condos.xml`)

O arquivo XML principal foi estruturado para fornecer todas as informações de um condomínio sem carregar ofertas de apartamentos ligadas a ele, mantendo os dados focados puramente na infraestrutura e localização:

```xml
<condominio>
  <id>hashId_unico</id>
  <slug>slug-url-amigavel</slug>
  <nome>Nome do Condomínio</nome>
  <descricao>Descrição textual de SEO da página...</descricao>
  <localizacao>
    <endereco>Nome da Rua/Av</endereco>
    <numero>Número</numero>
    <cep>CEP</cep>
    <bairro>Bairro</bairro>
    <cidade>Florianópolis</cidade>
    <estado>SC</estado>
    <latitude>Latitude Geográfica</latitude>
    <longitude>Longitude Geográfica</longitude>
  </localizacao>
  <caracteristicas>
    <area_min>Área Mínima</area_min>
    <area_max>Área Máxima</area_max>
    <quartos_min>Mínimo de Quartos</quartos_min>
    <quartos_max>Máximo de Quartos</quartos_max>
    ...
  </caracteristicas>
  <estrutura>
    <portaria>Tipo de Portaria</portaria>
    <itens>
      <item disponivel="SIM|NAO">Nome da Instalação/Facilidade</item>
    </itens>
  </estrutura>
  <fotos>
    <foto categoria="categoria_foto" legenda="Legenda">URL_da_Foto_Alta_Resolucao</foto>
  </fotos>
  <url_original>Link original do QuintoAndar</url_original>
</condominio>
```

---

## Como Baixar as Fotos do Condomínio

Como existem mais de 2.000 condomínios, fazer o download de todas as fotos (~20.000 imagens) ocupará cerca de **4.3 GB** de espaço em disco. Recomenda-se manter as referências das fotos apontando para as URLs absolutas no seu banco de dados ou baixá-las sob demanda.

Se você deseja fazer o download local das imagens de forma controlada, utilize o script `download_images.py`:

### 1. Executar com Limite para Testar (Padrão: 5 condomínios)
```bash
python3 scripts/download_images.py
```

### 2. Baixar Imagens de Mais Condomínios (ex: 50 condomínios)
```bash
python3 scripts/download_images.py --limit 50
```

### 3. Baixar Imagens de TODOS os Condomínios
```bash
python3 scripts/download_images.py --limit 0
```

*As imagens serão organizadas em pastas com o `slug` de cada condomínio dentro do diretório `/images/`.*

---

## Como Remover Marcas d'Água

Criamos um utilitário programático (`remove_watermarks.py`) que usa OpenCV em Python para analisar a região central das fotos, detectar o texto da marca d'água branca e aplicar inpainting para removê-lo.

### Pré-requisitos:
Instalar o OpenCV e o NumPy:
```bash
pip install opencv-python numpy
```

### Para limpar uma única foto:
```bash
python3 scripts/remove_watermarks.py --input images/slug_condominio/facade_1.jpg --output images/slug_condominio/facade_1_clean.jpg
```

### Para limpar toda a pasta de imagens baixadas:
```bash
python3 scripts/remove_watermarks.py --input images/ --output images_clean/
```

---

## API de Processamento de Imagens (FastAPI)

Desenvolvemos uma API HTTP de alta performance para remoção de marcas d'água em tempo real (em memória), evitando o acúmulo de arquivos temporários em disco.

### Instalação de Dependências
Para instalar as dependências necessárias para a API:
```bash
pip install -r requirements.txt
```

### Como Executar a API
Inicie o servidor uvicorn na porta `8000`:
```bash
uvicorn api.main:app --reload
```

A API estará acessível em:
- Documentação interativa (Swagger UI): `http://127.0.0.1:8000/docs`
- Health check: `GET http://127.0.0.1:8000/`

### Exemplos de Uso (Endpoints)

#### 1. Enviar arquivo de imagem local (`POST /clean-image`)
Envia uma imagem local do seu computador para ser limpa e retorna o arquivo de imagem limpo imediatamente.

```bash
curl -X POST "http://127.0.0.1:8000/clean-image" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@caminho/para/sua/imagem.jpg" \
     --output imagem_limpa.jpg
```

#### 2. Enviar URL de imagem externa (`POST /clean-image-url`)
Faz o download de uma imagem a partir de uma URL pública, remove a marca d'água e retorna a imagem limpa imediatamente.

```bash
curl -X POST "http://127.0.0.1:8000/clean-image-url" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://img.quintoandar.com.br/foto/1234567-facade.jpg"}' \
     --output imagem_limpa.jpg
```

---

## Como Enviar para o Seu GitHub

Recomenda-se **não** comitar a pasta `images/` ou `images_clean/` inteira no GitHub caso você baixe todas as fotos, pois repositórios do GitHub têm limite de tamanho de 1GB a 5GB e comitar mídias grandes prejudica a performance do controle de versão. Em produção, armazene as fotos em um serviço de CDN ou Storage (como AWS S3, Google Cloud Storage ou Firebase Storage).

Para subir o projeto no seu GitHub, siga os passos abaixo:

1. No terminal do seu computador, navegue até a pasta do projeto:
   ```bash
   cd quintoandar_florianopolis_condos
   ```

2. Inicialize o repositório git e comite os arquivos de dados e código:
   ```bash
   git init
   git add README.md data/ scripts/
   git commit -m "feat: adiciona dados estruturados e scripts de raspagem de condominios de Floripa"
   ```

3. Crie um repositório vazio no seu painel do GitHub chamado `quintoandar_florianopolis_condos`.

4. Conecte o repositório local ao GitHub e envie os arquivos (substitua o link pelo seu repositório):
   ```bash
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/quintoandar_florianopolis_condos.git
   git push -u origin main
   ```
