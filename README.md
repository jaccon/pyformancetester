# pyFormanceTester

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)

**pyFormanceTester** é uma ferramenta avançada para análise de performance de websites. Ela verifica tamanhos de imagens, CSS, JavaScript, tempos de carregamento e muito mais, gerando relatórios detalhados em diversos formatos.

## 📋 Índice

- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Parâmetros](#-parâmetros)
- [Tipos de Relatórios](#-tipos-de-relatórios)
- [Exemplos](#-exemplos)
- [Detecção de APIs](#-detecção-de-apis)
- [Estrutura do Código](#-estrutura-do-código)
- [Contribuições](#-contribuições)

## ✨ Características

- **Análise completa de recursos**: Detecta e analisa todos os recursos da página (HTML, imagens, CSS, JavaScript, etc.)
- **Métricas detalhadas**: Coleta informações de tamanho, tempo de carregamento, cabeçalhos HTTP, etc.
- **Análise de imagens**: Verifica dimensões, formatos e otimização de imagens
- **Detecção de APIs**: Identifica chamadas de API no código JavaScript e padrões de URL
- **Relatórios diversos**: Gera relatórios em CSV, HTML com Material Design e gráficos
- **Estatísticas HTTP**: Análise completa de códigos de status, tempos de resposta e tipos de conteúdo
- **Visualização de dados**: Gráficos interativos para melhor compreensão dos resultados
- **Listagem rápida**: Opção para listar rapidamente todos os recursos carregados

## 📋 Requisitos

- Python 3.9 ou superior
- Bibliotecas:
  - requests
  - beautifulsoup4
  - colorama
  - tqdm
  - Pillow (PIL)
  - matplotlib
  - jinja2

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/pyFormanceTester.git
cd pyFormanceTester
```

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

Se o arquivo `requirements.txt` não existir, você pode instalar as dependências manualmente:
```bash
pip install requests beautifulsoup4 colorama tqdm pillow matplotlib jinja2
```

## 🖥️ Uso

Execute o script passando a URL do site que deseja analisar:

```bash
python _test.py --url https://www.exemplo.com.br
```

Isso analisará o site e gerará relatórios detalhados na pasta `reports/`.

## 🎛️ Parâmetros

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `--url` | URL do site a ser analisado (obrigatório) | - |
| `--output` | Diretório para salvar relatórios | reports |
| `--detail-level` | Nível de detalhe das métricas (basic ou full) | full |
| `--timeout` | Timeout em segundos para requisições | 30 |
| `--user-agent` | User-Agent personalizado para as requisições | Padrão do requests |
| `--no-html` | Desativa a geração de relatório HTML | False |
| `--list-resources` | Exibe uma lista rápida com todos os recursos | False |
| `--list-format` | Formato da lista de recursos (text ou csv) | text |
| `--assets-table` | Exibe tabela completa com todos os assets, tamanhos (KB) e tempos (ms) | False |

## 📊 Tipos de Relatórios

### 1. Relatório CSV Principal
Contém todos os detalhes de cada recurso carregado, incluindo:
- URL
- Tamanho em KB
- Tempo de carregamento
- Tipo de conteúdo
- Cabeçalhos HTTP
- Métricas específicas (dimensões de imagens, scripts async/defer, etc.)

### 2. Relatório de APIs
Lista todas as APIs e chamadas XHR/AJAX detectadas, incluindo:
- URL da API
- Método de detecção
- Código de status
- Estrutura JSON (quando aplicável)

### 3. Relatório de Estatísticas HTTP
Resumo de métricas importantes como:
- Total de requisições
- Distribuição de códigos de status
- Tempos médios, mínimos e máximos de resposta
- Tipos de conteúdo

### 4. Relatório HTML com Material Design
Um relatório completo e visual com:
- Resumo geral do site
- Gráficos interativos
- Distribuição de recursos por tipo
- Tempos de carregamento
- Recursos mais pesados e mais lentos
- Recomendações de otimização

### 5. Listagem Rápida de Recursos
Uma visualização rápida de todos os recursos carregados, disponível em formato texto ou CSV.

### 6. Tabela de Assets Completa
Uma tabela detalhada e colorida de todos os assets, incluindo:
- Numeração sequencial
- Tipo de recurso
- URL
- Tamanho em kilobytes
- Tempo de carregamento em milissegundos
- Tipo MIME
- Código de status HTTP
- Status de cache

## 💡 Exemplos

### Análise básica
```bash
python _test.py --url https://www.exemplo.com.br
```

### Gerar apenas o relatório em CSV (sem HTML)
```bash
python _test.py --url https://www.exemplo.com.br --no-html
```

### Análise rápida com timeout reduzido
```bash
python _test.py --url https://www.exemplo.com.br --timeout 10 --detail-level basic
```

### Listar recursos de forma rápida
```bash
python _test.py --url https://www.exemplo.com.br --list-resources
```

### Exportar lista de recursos para CSV
```bash
python _test.py --url https://www.exemplo.com.br --list-resources --list-format csv
```

### Gerar tabela completa com todos os assets
```bash
python _test.py --url https://www.exemplo.com.br --assets-table
```

### Usar um User-Agent personalizado
```bash
python _test.py --url https://www.exemplo.com.br --user-agent "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
```

## 🔍 Detecção de APIs

O pyFormanceTester é capaz de detectar APIs em sites de várias formas:

1. **Análise de JavaScript**: Identifica padrões de chamadas como fetch(), XHR, axios, etc.
2. **Análise de URLs**: Detecta padrões comuns de URLs de API
3. **Verificação de endpoints conhecidos**: Testa endpoints comuns como /api, /v1, etc.
4. **Análise de conteúdo JSON**: Identifica respostas e estruturas típicas de APIs
5. **Detecção específica para e-commerce**: Encontra APIs de produtos, catálogos, etc.

Todas as APIs detectadas são categorizadas em:
- **XHR**: Chamadas XMLHttpRequest tradicionais
- **Fetch**: Chamadas usando a Fetch API
- **JSON**: Endpoints que retornam JSON
- **REST**: APIs RESTful
- **Products**: APIs específicas de produtos (e-commerce)

## 📁 Estrutura do Código

- `_test.py`: Script principal com todas as funcionalidades
- `templates/`: Contém o template HTML para o relatório com Material Design
- `reports/`: Diretório onde são salvos os relatórios gerados
  - `graphs/`: Gráficos gerados para o relatório HTML

## 👥 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Reportar bugs
2. Sugerir novos recursos
3. Enviar pull requests

## 📄 Licença

Este projeto está licenciado sob a licença MIT - consulte o arquivo LICENSE para obter detalhes.

---

Desenvolvido por André Jaccon
