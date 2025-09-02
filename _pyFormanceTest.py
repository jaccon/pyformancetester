#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import csv
import os
import sys
import time
import re
import io
import json
import statistics
import base64
import webbrowser
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from tqdm import tqdm
from PIL import Image
import matplotlib.pyplot as plt
from jinja2 import Template, Environment, FileSystemLoader

# Inicializar colorama para formatação de saída colorida
init(autoreset=True)


class WebsitePerformanceTester:
    def __init__(self, url, output_dir="reports"):
        """
        Inicializa o testador de desempenho com a URL fornecida
        """
        self.url = url
        self.base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        self.domain = urlparse(url).netloc
        # Carregar as configurações do arquivo config.json
        self.config = self._load_config()
        self.resources = {
            "images": [],
            "css": [],
            "js": [],
            "fonts": [],
            "videos": [],
            "others": []
        }
        # Novo dicionário para armazenar APIs e solicitações XHR/AJAX
        self.apis = {
            "xhr": [],      # XMLHttpRequests
            "fetch": [],    # Fetch API calls
            "json": [],     # JSON endpoints
            "rest": [],     # RESTful APIs
            "products": [], # APIs de produtos
            "graphql": []   # GraphQL APIs
        }
        self.output_dir = output_dir
        self.total_load_time = 0
        self.page_size = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
            'Accept': '*/*',  # Aceitar todos os tipos de conteúdo
            'Accept-Language': 'en-US,en;q=0.9,pt;q=0.8'
        })
        
        # Estatísticas gerais de HTTP
        self.http_stats = {
            "status_codes": {},
            "content_types": {},
            "response_times": [],
            "total_requests": 0,
            "failed_requests": 0
        }
        
        # Carregar as configurações do arquivo config.json
        self.config = self._load_config()
        
        # Lista para armazenar gráficos base64 para o relatório HTML
        self.graph_images = {}
        self.report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Criar diretórios de relatórios se não existirem
        self.graphs_dir = f"{output_dir}/graphs"
        self.templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if not os.path.exists(self.graphs_dir):
            os.makedirs(self.graphs_dir)
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
    
    def _load_config(self):
        """
        Carrega as configurações do arquivo config.json
        """
        default_config = {
            "theme": "default",  # Tema padrão (claro)
        }
        
        config_file = "config.json"
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"{Fore.GREEN}Configurações carregadas de {config_file}")
                # Mesclar com valores padrão para garantir que todas as configurações existam
                merged_config = {**default_config, **config}
                return merged_config
            else:
                print(f"{Fore.YELLOW}Arquivo de configuração não encontrado. Usando configurações padrão.")
                return default_config
        except Exception as e:
            print(f"{Fore.RED}Erro ao carregar configurações: {e}. Usando configurações padrão.")
            return default_config

    def analyze_website(self):
        """
        Analisa o site e coleta informações sobre seus recursos
        """
        print(f"{Fore.CYAN}Analisando o site: {self.url}")
        start_time = time.time()
        
        try:
            # Requisição inicial para obter o HTML da página
            response = self.session.get(self.url)
            response.raise_for_status()
            
            # Tempo de carregamento do HTML inicial
            html_load_time = time.time() - start_time
            self.page_size = len(response.content)
            
            print(f"{Fore.GREEN}HTML carregado em {html_load_time:.2f} segundos")
            print(f"{Fore.GREEN}Tamanho da página HTML: {self.page_size/1024:.2f} KB")
            
            # Registrar a requisição inicial nas estatísticas HTTP
            self._record_http_stats(response, html_load_time)
            
            # Parse do HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrair recursos
            self._extract_resources(soup)
            
            # Procurar possíveis APIs no JavaScript
            self._detect_apis(soup)
            
            # Analisar recursos encontrados e suas respostas HTTP
            self._analyze_resources()
            
            # Tentar acessar API endpoints conhecidos comuns
            self._probe_common_api_endpoints()
            
            # Analisar URLs para identificar padrões de API
            self._analyze_urls_for_api_patterns()
            
            # Calcular tempo total de carregamento
            self.total_load_time = time.time() - start_time
            print(f"{Fore.CYAN}Análise concluída em {self.total_load_time:.2f} segundos")
            
        except requests.RequestException as e:
            print(f"{Fore.RED}Erro ao acessar o site: {e}")
            self.http_stats["failed_requests"] += 1
            sys.exit(1)
    
    def _record_http_stats(self, response, load_time):
        """
        Registra estatísticas de respostas HTTP
        """
        status_code = response.status_code
        content_type = response.headers.get('content-type', 'unknown').split(';')[0]
        
        # Incrementar contador de status code
        self.http_stats["status_codes"][status_code] = self.http_stats["status_codes"].get(status_code, 0) + 1
        
        # Incrementar contador de content type
        self.http_stats["content_types"][content_type] = self.http_stats["content_types"].get(content_type, 0) + 1
        
        # Adicionar tempo de resposta
        self.http_stats["response_times"].append(load_time)
        
        # Incrementar total de requisições
        self.http_stats["total_requests"] += 1
    
    def _detect_apis(self, soup):
        """
        Analisa o JavaScript da página para detectar padrões de chamadas de API
        """
        print(f"{Fore.YELLOW}Procurando por chamadas de API no código JavaScript...")
        
        # Examinar scripts incorporados
        for script in soup.find_all('script'):
            if script.string:
                self._analyze_js_for_api_calls(script.string)
        
        # Baixar e analisar arquivos JavaScript externos
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                try:
                    full_url = urljoin(self.url, src)
                    response = self.session.get(full_url, timeout=10)
                    if response.status_code == 200:
                        self._analyze_js_for_api_calls(response.text, full_url)
                except Exception as e:
                    print(f"{Fore.RED}Erro ao analisar script externo {src}: {e}")
    
    def _analyze_js_for_api_calls(self, js_content, script_url=None):
        """
        Analisa o conteúdo JavaScript para encontrar padrões de chamadas de API
        """
        # Padrões para detectar chamadas de API em JavaScript
        api_patterns = {
            "fetch": r'fetch\([\'"]([^\'"]+)[\'"]',
            "xhr": r'\.open\([\'"](?:GET|POST|PUT|DELETE)[\'"],\s*[\'"]([^\'"]+)[\'"]',
            "ajax": r'\.ajax\(\s*{\s*url:\s*[\'"]([^\'"]+)[\'"]',
            "axios": r'axios\.(?:get|post|put|delete)\([\'"]([^\'"]+)[\'"]',
            "api_url": r'(?:api_url|apiUrl|API_URL|url|URL)[\'"]?\s*(?:=|:)\s*[\'"]([^\'"]+)[\'"]',
            "endpoint": r'(?:endpoint|Endpoint|ENDPOINT)[\'"]?\s*(?:=|:)\s*[\'"]([^\'"]+)[\'"]',
            "service_url": r'(?:service|serviceUrl|service_url)[\'"]?\s*(?:=|:)\s*[\'"]([^\'"]+)[\'"]',
            "graphql": r'(?:graphql|GraphQL)[\'"]?\s*(?:=|:)\s*[\'"]([^\'"]+)[\'"]',
            "products": r'(?:products|product|productId|productIds)[\'"]?\s*(?:=|:)\s*[\'"]([^\'"]+)[\'"]'
        }
        
        for pattern_name, pattern in api_patterns.items():
            matches = re.findall(pattern, js_content)
            for match in matches:
                full_url = urljoin(self.url, match)
                
                # Determinar o tipo de API com base no padrão e URL
                api_type = "xhr"  # Padrão
                
                # Verificar se é uma API de produtos (muito comum em sites de e-commerce)
                if "product" in match.lower() or "sku" in match.lower() or "catalog" in match.lower():
                    api_type = "products"
                # Verificar se é API JSON ou API REST
                elif "json" in match.lower() or "api" in match.lower():
                    api_type = "json"
                elif "/api/" in match or "/v1/" in match or "/v2/" in match or "/rest/" in match:
                    api_type = "rest"
                elif "/graphql" in match.lower() or "/gql" in match.lower():
                    api_type = "graphql"
                elif pattern_name == "fetch":
                    api_type = "fetch"
                elif pattern_name == "products":
                    api_type = "products"
                
                # Adicionar à lista apropriada se ainda não existe
                if full_url not in [api["url"] for api in self.apis[api_type]]:
                    self.apis[api_type].append({
                        "url": full_url,
                        "pattern_detected": pattern_name,
                        "source_script": script_url,
                        "analyzed": False
                    })
    
    def _probe_common_api_endpoints(self):
        """
        Tenta acessar endpoints comuns de API para verificar existência
        """
        print(f"{Fore.YELLOW}Verificando endpoints comuns de API...")
        
        common_endpoints = [
            "/api",
            "/api/v1",
            "/api/v2",
            "/v1",
            "/v2",
            "/rest",
            "/graphql",
            "/data",
            "/service",
            "/services",
            "/wp-json",  # WordPress REST API
            "/produtos",  # Produtos (PT)
            "/products",  # Produtos (EN)
            "/product",   # Produto singular
            "/catalog",   # Catálogo 
            "/catalogo",  # Catálogo (PT)
            "/vitrine",   # Vitrine (PT)
            "/showcase"   # Vitrine (EN)
        ]
        
        for endpoint in common_endpoints:
            try:
                url = urljoin(self.url, endpoint)
                start_time = time.time()
                response = self.session.get(url, timeout=5, allow_redirects=False)
                load_time = time.time() - start_time
                
                # Registrar estatísticas HTTP
                self._record_http_stats(response, load_time)
                
                # Verificar se parece uma API por tipo de conteúdo ou status code
                is_api = False
                content_type = response.headers.get('content-type', '').lower()
                
                if 'application/json' in content_type or 'application/xml' in content_type:
                    is_api = True
                elif response.status_code == 200:
                    # Tentar analisar como JSON
                    try:
                        json_data = response.json()
                        is_api = True
                    except:
                        pass
                
                if is_api:
                    api_type = "rest" if "json" in content_type else "xhr"
                    self.apis[api_type].append({
                        "url": url,
                        "pattern_detected": "common_endpoint",
                        "status_code": response.status_code,
                        "content_type": content_type,
                        "load_time": load_time,
                        "size": len(response.content),
                        "analyzed": True
                    })
            except Exception as e:
                # Ignorar erros silenciosamente durante a sondagem
                pass
    
    def _analyze_urls_for_api_patterns(self):
        """
        Analisa todas as URLs dos recursos para identificar padrões comuns de API
        """
        print(f"{Fore.YELLOW}Analisando URLs para identificar possíveis APIs...")
        
        # Padrões comuns que indicam que uma URL é uma API
        api_url_patterns = [
            r'\.json($|\?)',                    # Termina com .json
            r'/api/',                           # Contém /api/
            r'/rest/',                          # Contém /rest/
            r'/graphql',                        # GraphQL endpoint
            r'/v[0-9]+/',                       # Versão da API (/v1/, /v2/, etc)
            r'/product(?:s|os)?/',              # Produtos (inglês/português)
            r'/catalog(?:o)?/',                 # Catálogo (inglês/português)
            r'/data/',                          # Endpoint de dados
            r'/services?/',                     # Serviços
            r'/[^/]+\.php\?',                   # Script PHP com parâmetros
            r'/(?:get|fetch|search|query)[A-Z]' # getNomeRecurso, fetchData, etc
        ]
        
        api_url_regex = '|'.join(api_url_patterns)
        
        # Analisar todas as URLs dos recursos
        for resource_type, resources in self.resources.items():
            for resource in resources:
                url = resource.get('url', '')
                
                # Verificar se a URL corresponde a algum padrão de API
                if re.search(api_url_regex, url, re.IGNORECASE):
                    # Determinar o tipo de API com base no padrão identificado
                    api_type = "rest"  # Padrão
                    
                    # Análise mais específica do tipo de API
                    if "graphql" in url.lower():
                        api_type = "graphql"
                    elif "product" in url.lower() or "produto" in url.lower() or "catalog" in url.lower():
                        api_type = "products"
                    elif ".json" in url.lower():
                        api_type = "json"
                    
                    # Adicionar à lista de APIs se ainda não existir
                    if url not in [api["url"] for api in self.apis[api_type]]:
                        self.apis[api_type].append({
                            "url": url,
                            "pattern_detected": "url_pattern",
                            "source": resource_type,
                            "analyzed": False
                        })
    
    def _extract_resources(self, soup):
        """
        Extrai recursos (imagens, CSS, JS, fontes, vídeos, etc.) do HTML
        """
        print(f"{Fore.YELLOW}Extraindo recursos da página...")
        
        # Extrair imagens
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                full_url = urljoin(self.url, src)
                img_data = {
                    'url': full_url,
                    'element_type': 'img',
                    'alt_text': img.get('alt', ''),
                    'width': img.get('width', ''),
                    'height': img.get('height', ''),
                    'loading': img.get('loading', '')
                }
                self.resources['images'].append(img_data)
        
        # Extrair CSS
        for css in soup.find_all('link', rel='stylesheet'):
            href = css.get('href')
            if href:
                full_url = urljoin(self.url, href)
                self.resources['css'].append({
                    'url': full_url,
                    'element_type': 'css',
                    'media': css.get('media', 'all'),
                    'integrity': css.get('integrity', '')
                })
        
        # Extrair JavaScript
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                full_url = urljoin(self.url, src)
                self.resources['js'].append({
                    'url': full_url,
                    'element_type': 'js',
                    'async': 'async' if script.get('async') else 'false',
                    'defer': 'defer' if script.get('defer') else 'false',
                    'type': script.get('type', 'text/javascript')
                })
        
        # Extrair fontes
        for font in soup.find_all('link', rel=lambda x: x and 'font' in x):
            href = font.get('href')
            if href:
                full_url = urljoin(self.url, href)
                self.resources['fonts'].append({
                    'url': full_url,
                    'element_type': 'font'
                })
        
        # Extrair recursos de estilo @import dentro de CSS
        for style in soup.find_all('style'):
            style_text = style.string
            if style_text:
                import_urls = re.findall(r'@import\s+[\'"]([^\'"]+)[\'"]', style_text)
                for url in import_urls:
                    full_url = urljoin(self.url, url)
                    self.resources['css'].append({
                        'url': full_url,
                        'element_type': 'css-import'
                    })
        
        # Extrair vídeos
        for video in soup.find_all(['video', 'source']):
            src = video.get('src')
            if src:
                full_url = urljoin(self.url, src)
                self.resources['videos'].append({
                    'url': full_url,
                    'element_type': 'video',
                    'type': video.get('type', '')
                })
        
        # Extrair outros recursos (iframes, objetos, etc.)
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src:
                full_url = urljoin(self.url, src)
                self.resources['others'].append({
                    'url': full_url,
                    'element_type': 'iframe'
                })
                
        print(f"{Fore.GREEN}Recursos encontrados:")
        print(f"  - Imagens: {len(self.resources['images'])}")
        print(f"  - CSS: {len(self.resources['css'])}")
        print(f"  - JavaScript: {len(self.resources['js'])}")
        print(f"  - Fontes: {len(self.resources['fonts'])}")
        print(f"  - Vídeos: {len(self.resources['videos'])}")
        print(f"  - Outros: {len(self.resources['others'])}")

    def _analyze_resources(self):
        """
        Analisa cada recurso encontrado para obter tamanho, tempo de carregamento e métricas detalhadas
        """
        print(f"{Fore.YELLOW}Analisando recursos...")
        
        all_resources = []
        for resource_type, resources in self.resources.items():
            all_resources.extend(resources)
        
        # Adicionar também as APIs detectadas para análise
        api_resources = []
        for api_type, apis in self.apis.items():
            for api in apis:
                if not api.get("analyzed", False):
                    api["resource_type"] = api_type
                    api_resources.append(api)
        
        print(f"{Fore.GREEN}Analisando {len(all_resources)} recursos e {len(api_resources)} possíveis APIs...")
        
        # Analisar todos os recursos normais
        for resource in tqdm(all_resources, desc="Analisando recursos"):
            self._analyze_single_resource(resource)
            
        # Analisar APIs detectadas
        if api_resources:
            for api in tqdm(api_resources, desc="Analisando APIs"):
                self._analyze_single_resource(api, is_api=True)
                api["analyzed"] = True
    
    def _analyze_single_resource(self, resource, is_api=False):
        """
        Analisa um único recurso para obter informações detalhadas
        """
        try:
            start_time = time.time()
            # Usar a sessão para aproveitar a conexão persistente
            headers = {}
            
            # Para APIs, adicionar cabeçalhos específicos
            if is_api:
                headers = {
                    'Accept': 'application/json, application/xml, */*',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            
            # Primeira tentativa com HEAD para minimizar transferência de dados
            response = self.session.head(resource['url'], timeout=10, headers=headers)
            
            # Para APIs e recursos que não funcionam bem com HEAD, usar GET
            if is_api or response.status_code != 200:
                response = self.session.get(resource['url'], timeout=10, stream=True, headers=headers)
            
            load_time = time.time() - start_time
            
            # Registrar nas estatísticas HTTP
            self._record_http_stats(response, load_time)
            
            # Coletar informações dos cabeçalhos
            headers = response.headers
            content_type = headers.get('content-type', 'unknown')
            resource['content_type'] = content_type
            resource['server'] = headers.get('server', 'unknown')
            
            # Informações de cache
            resource['cache_control'] = headers.get('cache-control', 'not-specified')
            resource['etag'] = headers.get('etag', 'not-specified')
            resource['expires'] = headers.get('expires', 'not-specified')
            resource['last_modified'] = headers.get('last-modified', 'not-specified')
            
            # Informações de compressão
            resource['content_encoding'] = headers.get('content-encoding', 'none')
            
            # Informações de segurança e CORS
            resource['x_content_type_options'] = headers.get('x-content-type-options', 'not-specified')
            resource['strict_transport_security'] = headers.get('strict-transport-security', 'not-specified')
            resource['access_control_allow_origin'] = headers.get('access-control-allow-origin', 'not-specified')
            
            # Informações de conexão
            resource['connection'] = headers.get('connection', 'not-specified')
            
            # Tentar obter o tamanho do recurso
            if 'content-length' in headers:
                size = int(headers['content-length'])
            else:
                # Se o content-length não estiver disponível, fazer download do recurso
                if not hasattr(response, 'content'):
                    response = self.session.get(resource['url'], timeout=10)
                size = len(response.content)
            
            # Adicionar informações básicas ao recurso
            resource['size'] = size
            resource['load_time'] = load_time
            resource['status_code'] = response.status_code
            resource['time_to_first_byte'] = response.elapsed.total_seconds()
            resource['redirects'] = len(response.history) if hasattr(response, 'history') else 0
            
            # Para APIs, tentar analisar o conteúdo como JSON
            if is_api or 'application/json' in content_type.lower():
                try:
                    if not hasattr(response, 'content'):
                        response = self.session.get(resource['url'], timeout=10)
                    
                    json_data = json.loads(response.text)
                    resource['is_json'] = True
                    
                    # Extrair informações básicas sobre a estrutura do JSON
                    if isinstance(json_data, dict):
                        resource['json_keys'] = list(json_data.keys())[:10]  # Primeiras 10 chaves
                        resource['json_structure'] = 'object'
                        
                        # Detecção de APIs de produtos com base nas chaves do JSON
                        product_keys = ['product', 'products', 'sku', 'items', 'catalog', 
                                       'price', 'stock', 'inventory', 'categoria', 'category']
                        api_keys = ['api', 'data', 'results', 'pagination', 'meta', 'response']
                        
                        # Verificar se é uma API de produtos
                        if any(key.lower() in product_keys for key in json_data.keys()):
                            # Este é um recurso de produtos, vamos adicioná-lo à lista de APIs
                            if not is_api:  # Se ainda não foi identificado como API
                                url = resource['url']
                                if url not in [api["url"] for api in self.apis["products"]]:
                                    self.apis["products"].append({
                                        "url": url,
                                        "pattern_detected": "json_content_analysis",
                                        "content_type": content_type,
                                        "analyzed": True,
                                        "status_code": resource.get('status_code', 0),
                                        "load_time": resource.get('load_time', 0),
                                        "size": resource.get('size', 0)
                                    })
                    elif isinstance(json_data, list):
                        resource['json_structure'] = 'array'
                        resource['json_length'] = len(json_data)
                        
                        # Se a lista contém dicionários com chaves relacionadas a produtos
                        if len(json_data) > 0 and isinstance(json_data[0], dict):
                            sample_keys = set()
                            for item in json_data[:5]:  # Analisar os primeiros 5 itens
                                if isinstance(item, dict):
                                    sample_keys.update(item.keys())
                            
                            # Verificar se tem chaves típicas de produtos
                            product_item_keys = ['id', 'name', 'price', 'sku', 'image', 'description', 
                                               'nome', 'preco', 'imagem', 'categoria']
                            if any(key.lower() in product_item_keys for key in sample_keys):
                                # Este parece ser uma API de produtos
                                url = resource['url']
                                if url not in [api["url"] for api in self.apis["products"]]:
                                    self.apis["products"].append({
                                        "url": url,
                                        "pattern_detected": "json_array_analysis",
                                        "content_type": content_type,
                                        "analyzed": True,
                                        "status_code": resource.get('status_code', 0),
                                        "load_time": resource.get('load_time', 0),
                                        "size": resource.get('size', 0)
                                    })
                    
                except (json.JSONDecodeError, UnicodeDecodeError):
                    resource['is_json'] = False
            
            # Para imagens, obter dimensões e formato
            if resource.get('element_type') == 'img' and 'image' in content_type.lower():
                try:
                    # Somente baixar a imagem se ainda não baixou
                    if not hasattr(response, 'content'):
                        response = self.session.get(resource['url'], timeout=10)
                        
                    img = Image.open(io.BytesIO(response.content))
                    resource['img_width'] = img.width
                    resource['img_height'] = img.height
                    resource['img_format'] = img.format
                    resource['img_mode'] = img.mode
                    resource['img_colors'] = len(img.getcolors(maxcolors=65536)) if img.getcolors(maxcolors=65536) else 'more than 65536'
                    resource['img_aspect_ratio'] = round(img.width / img.height, 2) if img.height > 0 else 0
                except Exception as img_e:
                    resource['img_error'] = str(img_e)
            
        except Exception as e:
            resource['size'] = 0
            resource['load_time'] = 0
            resource['status_code'] = 0
            resource['error'] = str(e)
            self.http_stats["failed_requests"] += 1

    def generate_report(self):
        """
        Gera relatório CSV com os resultados da análise e gráficos
        """
        timestamp = self.report_timestamp
        domain = self.domain.replace(".", "_")
        
        # Gerar relatório CSV principal
        main_filename = f"{self.output_dir}/performance_report_{domain}_{timestamp}.csv"
        api_filename = f"{self.output_dir}/api_report_{domain}_{timestamp}.csv"
        http_stats_filename = f"{self.output_dir}/http_stats_{domain}_{timestamp}.csv"
        html_filename = f"{self.output_dir}/performance_report_{domain}_{timestamp}.html"
        
        print(f"{Fore.CYAN}Gerando relatórios...")
        
        # Definir todos os campos possíveis para o CSV principal
        fieldnames = [
            'tipo', 'url', 'tamanho_kb', 'tempo_carregamento_s', 'time_to_first_byte_s',
            'status_code', 'content_type', 'server', 'cache_control', 'etag', 'expires',
            'last_modified', 'content_encoding', 'element_type', 'media', 'integrity',
            'async', 'defer', 'type', 'alt_text', 'loading', 'redirects',
            'img_width', 'img_height', 'img_format', 'img_mode', 'img_colors',
            'img_aspect_ratio', 'error', 'connection', 'x_content_type_options',
            'strict_transport_security', 'access_control_allow_origin'
        ]
        
        # Gerar o relatório CSV principal
        with open(main_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Adicionar dados da página HTML principal
            writer.writerow({
                'tipo': 'html',
                'url': self.url,
                'tamanho_kb': round(self.page_size / 1024, 2),
                'tempo_carregamento_s': round(self.total_load_time, 2),
                'status_code': 200,
                'content_type': 'text/html'
            })
            
            # Adicionar dados de todos os recursos
            for resource_type, resources in self.resources.items():
                for resource in resources:
                    # Criar um dicionário com todos os dados do recurso
                    resource_data = {
                        'tipo': resource_type,
                        'url': resource['url'],
                        'tamanho_kb': round(resource.get('size', 0) / 1024, 2),
                        'tempo_carregamento_s': round(resource.get('load_time', 0), 2),
                        'time_to_first_byte_s': round(resource.get('time_to_first_byte', 0), 3),
                        'status_code': resource.get('status_code', 0),
                        'redirects': resource.get('redirects', 0)
                    }
                    
                    # Adicionar todos os campos extras disponíveis
                    for field in fieldnames:
                        if field in resource and field not in resource_data:
                            resource_data[field] = resource[field]
                    
                    writer.writerow(resource_data)
        
        # Gerar relatório específico para APIs
        api_fieldnames = [
            'tipo', 'url', 'pattern_detected', 'source_script', 'status_code', 
            'tamanho_kb', 'tempo_carregamento_s', 'time_to_first_byte_s', 
            'content_type', 'is_json', 'json_structure', 'json_keys', 'json_length',
            'cache_control', 'server', 'access_control_allow_origin', 'error'
        ]
        
        with open(api_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=api_fieldnames)
            writer.writeheader()
            
            # Adicionar dados de todas as APIs
            for api_type, apis in self.apis.items():
                for api in apis:
                    if api.get('analyzed', False):
                        api_data = {
                            'tipo': api_type,
                            'url': api['url'],
                            'pattern_detected': api.get('pattern_detected', ''),
                            'source_script': api.get('source_script', ''),
                            'status_code': api.get('status_code', 0),
                            'tamanho_kb': round(api.get('size', 0) / 1024, 2),
                            'tempo_carregamento_s': round(api.get('load_time', 0), 2),
                            'time_to_first_byte_s': round(api.get('time_to_first_byte', 0), 3),
                            'content_type': api.get('content_type', 'unknown'),
                            'is_json': api.get('is_json', False),
                            'json_structure': api.get('json_structure', ''),
                            'json_keys': ', '.join(api.get('json_keys', [])) if api.get('json_keys') else '',
                            'json_length': api.get('json_length', 0),
                            'cache_control': api.get('cache_control', 'not-specified'),
                            'server': api.get('server', 'unknown'),
                            'access_control_allow_origin': api.get('access_control_allow_origin', 'not-specified'),
                            'error': api.get('error', '')
                        }
                        writer.writerow(api_data)
        
        # Gerar relatório de estatísticas HTTP
        with open(http_stats_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Cabeçalho
            writer.writerow(['Métrica', 'Valor'])
            
            # Estatísticas gerais
            writer.writerow(['Total de Requisições', self.http_stats['total_requests']])
            writer.writerow(['Requisições com Falha', self.http_stats['failed_requests']])
            
            # Tempos de resposta
            if self.http_stats['response_times']:
                writer.writerow(['Tempo Médio de Resposta (s)', round(statistics.mean(self.http_stats['response_times']), 3)])
                writer.writerow(['Tempo Mínimo de Resposta (s)', round(min(self.http_stats['response_times']), 3)])
                writer.writerow(['Tempo Máximo de Resposta (s)', round(max(self.http_stats['response_times']), 3)])
                if len(self.http_stats['response_times']) > 1:
                    writer.writerow(['Desvio Padrão (s)', round(statistics.stdev(self.http_stats['response_times']), 3)])
            
            # Status codes
            writer.writerow(['', ''])
            writer.writerow(['Códigos de Status HTTP', 'Contagem'])
            for status_code, count in sorted(self.http_stats['status_codes'].items()):
                writer.writerow([status_code, count])
            
            # Content types
            writer.writerow(['', ''])
            writer.writerow(['Tipos de Conteúdo', 'Contagem'])
            for content_type, count in sorted(self.http_stats['content_types'].items(), key=lambda x: x[1], reverse=True):
                writer.writerow([content_type, count])
        
        # Gerar gráficos
        self._generate_graphs(timestamp, domain)
        
        # Gerar relatório HTML
        html_report_path = self._generate_html_report(html_filename)
        
        print(f"{Fore.GREEN}Relatório principal gerado com sucesso: {main_filename}")
        print(f"{Fore.GREEN}Relatório de APIs gerado com sucesso: {api_filename}")
        print(f"{Fore.GREEN}Relatório de estatísticas HTTP gerado com sucesso: {http_stats_filename}")
        print(f"{Fore.GREEN}Relatório HTML gerado com sucesso: {html_filename}")
        
        # Armazenar o timestamp do relatório para uso no método main
        self.report_timestamp = timestamp
        
        return main_filename, html_report_path
    
    def _generate_html_report(self, html_filename):
        """
        Gera um relatório HTML com Material Design
        """
        # Verificar se o template existe
        template_path = os.path.join(self.templates_dir, 'report_template.html')
        if not os.path.exists(template_path):
            print(f"{Fore.RED}Erro: Template HTML não encontrado em {template_path}")
            return
        
        self.report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Carregar o template
            with open(template_path, 'r', encoding='utf-8') as file:
                template_content = file.read()
            
            template = Template(template_content)
            
            # Calcular estatísticas para o template
            total_resources = sum(len(resources) for resources in self.resources.values())
            total_size = self.page_size + sum(
                resource.get('size', 0) for resource_type in self.resources.values() 
                for resource in resource_type
            )
            total_size_mb = round(total_size / 1024 / 1024, 2)
            
            # Estatísticas de cache
            cached_resources = sum(1 for resource_type in self.resources.values() 
                                 for resource in resource_type 
                                 if 'max-age' in resource.get('cache_control', ''))
            
            cached_percent = round(cached_resources / total_resources * 100, 1) if total_resources > 0 else 0
            
            # Estatísticas de compressão
            compressed_resources = sum(1 for resource_type in self.resources.values() 
                                      for resource in resource_type 
                                      if resource.get('content_encoding') not in ['none', None, ''])
            
            compressed_percent = round(compressed_resources / total_resources * 100, 1) if total_resources > 0 else 0
            
            # Estatísticas por tipo de recurso
            resource_stats = {}
            for resource_type, resources in self.resources.items():
                if resources:
                    type_size = sum(resource.get('size', 0) for resource in resources)
                    type_time = sum(resource.get('load_time', 0) for resource in resources)
                    
                    stats = {
                        'count': len(resources),
                        'total_size_kb': round(type_size / 1024, 2),
                        'avg_time': round(type_time / len(resources), 2)
                    }
                    
                    # Estatísticas específicas para cada tipo
                    if resource_type == 'images':
                        # Formatos de imagem
                        formats = {}
                        for img in resources:
                            fmt = img.get('img_format', 'Unknown')
                            formats[fmt] = formats.get(fmt, 0) + 1
                        stats['formats'] = formats
                        
                        # Imagens sem texto alternativo
                        no_alt = sum(1 for img in resources if not img.get('alt_text'))
                        stats['no_alt_text'] = no_alt
                        
                    elif resource_type == 'js':
                        # Scripts async/defer
                        stats['async_scripts'] = sum(1 for js in resources if js.get('async') == 'async')
                        stats['defer_scripts'] = sum(1 for js in resources if js.get('defer') == 'defer')
                    
                    resource_stats[resource_type] = stats
            
            # API data
            api_data = {}
            total_apis = 0
            for api_type, apis in self.apis.items():
                analyzed_apis = [api for api in apis if api.get('analyzed', False)]
                if analyzed_apis:
                    simplified_apis = []
                    for api in analyzed_apis:
                        simplified_api = {
                            'url': api['url'],
                            'status_code': api.get('status_code', 0),
                            'load_time': round(api.get('load_time', 0), 2),
                            'size_kb': round(api.get('size', 0) / 1024, 2),
                            'content_type': api.get('content_type', 'unknown')
                        }
                        simplified_apis.append(simplified_api)
                    
                    api_data[api_type] = simplified_apis
                    total_apis += len(analyzed_apis)
            
            # Recursos mais lentos
            all_resources = []
            for resource_type, resources in self.resources.items():
                for resource in resources:
                    all_resources.append({
                        'tipo': resource_type,
                        'url': resource['url'],
                        'load_time': round(resource.get('load_time', 0), 2),
                        'size_kb': round(resource.get('size', 0) / 1024, 2),
                        'status_code': resource.get('status_code', 0)
                    })
            
            # Top 10 recursos mais lentos
            slowest_resources = sorted(all_resources, key=lambda x: x['load_time'], reverse=True)[:10]
            
            # Top 10 recursos maiores
            largest_resources = sorted(all_resources, key=lambda x: x['size_kb'], reverse=True)[:10]
            
            # Estatísticas de tempo de resposta
            response_times = self.http_stats['response_times']
            response_time_stats = {
                'avg': round(statistics.mean(response_times), 3) if response_times else 0,
                'min': round(min(response_times), 3) if response_times else 0,
                'max': round(max(response_times), 3) if response_times else 0,
                'stddev': round(statistics.stdev(response_times), 3) if len(response_times) > 1 else 0
            }
            
            # Top tipos de conteúdo
            sorted_content_types = sorted(
                self.http_stats['content_types'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Preparar dados de todos os recursos para incluir no HTML
            all_resources = []
            
            # Adicionar página HTML principal
            html_load_time_ms = round(self.total_load_time * 1000, 2)
            all_resources.append({
                'tipo': 'html',
                'url': self.url,
                'tamanho_kb': round(self.page_size / 1024, 2),
                'tempo_ms': html_load_time_ms,
                'mime_type': 'text/html',
                'status': '200',
                'cache': self.main_page_response.headers.get('Cache-Control', 'N/A') if hasattr(self, 'main_page_response') else 'N/A'
            })
            
            # Adicionar todos os outros recursos
            resource_type_mapping = {
                'images': 'img',
                'css': 'css',
                'js': 'js',
                'fonts': 'font',
                'videos': 'media',
                'others': 'other'
            }
            
            for resource_type, resources in self.resources.items():
                for resource in resources:
                    tipo_simplificado = resource_type_mapping.get(resource_type, 'other')
                    load_time_ms = round(resource.get('load_time', 0) * 1000, 2)
                    
                    all_resources.append({
                        'tipo': tipo_simplificado,
                        'url': resource.get('url', 'N/A'),
                        'tamanho_kb': round(resource.get('size', 0) / 1024, 2),
                        'tempo_ms': load_time_ms,
                        'mime_type': resource.get('content_type', 'N/A'),
                        'status': str(resource.get('status_code', 'N/A')),
                        'cache': resource.get('cache_control', 'N/A')
                    })
            
            # Adicionar APIs
            for api_type, apis in self.apis.items():
                for api in apis:
                    if api.get('analyzed', False):
                        load_time_ms = round(api.get('load_time', 0) * 1000, 2)
                        all_resources.append({
                            'tipo': 'api',
                            'url': api.get('url', 'N/A'),
                            'tamanho_kb': round(api.get('size', 0) / 1024, 2),
                            'tempo_ms': load_time_ms,
                            'mime_type': api.get('content_type', 'application/json'),
                            'status': str(api.get('status_code', 'N/A')),
                            'cache': api.get('cache_control', 'N/A')
                        })
            
            # Obter o tema das configurações
            theme = self.config.get('theme', 'default')
            
            # Renderizar o template
            rendered_html = template.render(
                title=f"PyFormanceTester - {self.domain}",
                url=self.url,
                domain=self.domain,
                datetime_now=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                total_resources=total_resources,
                total_size_mb=total_size_mb,
                total_load_time=round(self.total_load_time, 2),
                html_load_time=round(self.total_load_time - sum(resource.get('load_time', 0) for resource_type in self.resources.values() for resource in resource_type), 2),
                cached_resources=cached_resources,
                cached_percent=cached_percent,
                compressed_resources=compressed_resources,
                compressed_percent=compressed_percent,
                resource_stats=resource_stats,
                http_stats=self.http_stats,
                response_time_avg=response_time_stats['avg'],
                response_time_min=response_time_stats['min'],
                response_time_max=response_time_stats['max'],
                response_time_stddev=response_time_stats['stddev'],
                content_types=dict(sorted_content_types),
                total_apis=total_apis,
                api_data=api_data,
                slowest_resources=slowest_resources,
                largest_resources=largest_resources,
                graph_images=self.graph_images,
                all_resources=all_resources,  # Adicionando a lista completa de recursos
                theme=theme  # Passando o tema das configurações para o template
            )
            
            # Salvar o HTML
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(rendered_html)
            
            print(f"{Fore.GREEN}Relatório HTML gerado com Material Design")
            
            # Retornar o caminho do relatório para uso posterior
            return html_filename
            
        except Exception as e:
            print(f"{Fore.RED}Erro ao gerar relatório HTML: {e}")
            import traceback
            traceback.print_exc()
    
    def generate_assets_table(self):
        """
        Gera uma tabela completa com todos os assets carregados do site
        Inclui caminhos, tamanhos em KB e tempos de carregamento em ms
        
        Returns:
            str: Texto formatado da tabela de assets
        """
        print(f"{Fore.YELLOW}Gerando tabela completa de assets...")
        
        # Cabeçalho da tabela
        output = f"\n{Fore.CYAN}{'=' * 100}\n"
        output += f"{Fore.CYAN}TABELA COMPLETA DE ASSETS: {self.url}\n"
        output += f"{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}\n\n"
        
        # Definir formato da tabela
        headers = ['#', 'Tipo', 'URL', 'Tamanho (KB)', 'Tempo (ms)', 'MIME Type', 'Status', 'Cache']
        
        # Preparar dados
        all_assets = []
        
        # Adicionar HTML principal
        all_assets.append({
            'tipo': 'HTML',
            'url': self.url,
            'tamanho_kb': round(self.page_size / 1024, 2),
            'tempo_ms': round(self.total_load_time * 1000, 2),
            'mime_type': 'text/html',
            'status': 200,
            'cache': 'N/A'
        })
        
        # Adicionar todos os outros recursos
        for resource_type, resources in self.resources.items():
            for resource in resources:
                all_assets.append({
                    'tipo': resource_type,
                    'url': resource.get('url', 'N/A'),
                    'tamanho_kb': round(resource.get('size', 0) / 1024, 2),
                    'tempo_ms': round(resource.get('load_time', 0) * 1000, 2),
                    'mime_type': resource.get('content_type', 'unknown'),
                    'status': resource.get('status_code', 'N/A'),
                    'cache': 'Sim' if 'max-age' in resource.get('cache_control', '') else 'Não'
                })
        
        # Ordenar por tamanho (decrescente)
        all_assets.sort(key=lambda x: x['tamanho_kb'], reverse=True)
        
        # Preparar a tabela formatada
        col_widths = {
            'num': 4,
            'tipo': 8,
            'url': 50,
            'tamanho': 12,
            'tempo': 12,
            'mime': 20,
            'status': 6,
            'cache': 6
        }
        
        # Formato de linha da tabela
        row_format = (f"{{:{col_widths['num']}}} {{:{col_widths['tipo']}}} " +
                     f"{{:{col_widths['url']}}} {{:{col_widths['tamanho']}}} " +
                     f"{{:{col_widths['tempo']}}} {{:{col_widths['mime']}}} " +
                     f"{{:{col_widths['status']}}} {{:{col_widths['cache']}}}")
        
        # Cabeçalho
        output += f"{Fore.GREEN}{row_format.format('#', 'TIPO', 'URL', 'TAMANHO (KB)', 'TEMPO (MS)', 'MIME TYPE', 'STATUS', 'CACHE')}{Style.RESET_ALL}\n"
        output += "-" * 120 + "\n"
        
        # Dados
        for i, asset in enumerate(all_assets, 1):
            # Truncar URL se muito longa
            url = asset['url']
            if len(url) > col_widths['url']:
                url = "..." + url[-(col_widths['url']-3):]
            
            # Truncar MIME type se muito longo
            mime = str(asset['mime_type'])
            if len(mime) > col_widths['mime']:
                mime = mime[:col_widths['mime']-3] + "..."
            
            # Formatar valores numéricos
            tamanho_str = f"{asset['tamanho_kb']:.2f}"
            tempo_str = f"{asset['tempo_ms']:.2f}"
            
            # Colorir com base no tamanho e tempo
            if asset['tamanho_kb'] > 500:
                tamanho_str = f"{Fore.RED}{tamanho_str}{Style.RESET_ALL}"
            elif asset['tamanho_kb'] > 200:
                tamanho_str = f"{Fore.YELLOW}{tamanho_str}{Style.RESET_ALL}"
                
            if asset['tempo_ms'] > 1000:
                tempo_str = f"{Fore.RED}{tempo_str}{Style.RESET_ALL}"
            elif asset['tempo_ms'] > 300:
                tempo_str = f"{Fore.YELLOW}{tempo_str}{Style.RESET_ALL}"
                
            # Status colorido
            status_str = str(asset['status'])
            if str(asset['status']).startswith('2'):
                status_str = f"{Fore.GREEN}{status_str}{Style.RESET_ALL}"
            elif str(asset['status']).startswith('3'):
                status_str = f"{Fore.BLUE}{status_str}{Style.RESET_ALL}"
            elif str(asset['status']).startswith('4') or str(asset['status']).startswith('5'):
                status_str = f"{Fore.RED}{status_str}{Style.RESET_ALL}"
                
            # Cache
            cache_str = asset['cache']
            if cache_str == 'Não':
                cache_str = f"{Fore.RED}{cache_str}{Style.RESET_ALL}"
            else:
                cache_str = f"{Fore.GREEN}{cache_str}{Style.RESET_ALL}"
                
            # Adicionar linha
            output += row_format.format(
                str(i), 
                asset['tipo'], 
                url, 
                tamanho_str, 
                tempo_str,
                mime, 
                status_str, 
                cache_str
            ) + "\n"
            
        # Estatísticas
        total_size_mb = sum(asset['tamanho_kb'] for asset in all_assets) / 1024
        avg_load_time = statistics.mean(asset['tempo_ms'] for asset in all_assets)
        
        output += f"\n{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}\n"
        output += f"Total de assets: {len(all_assets)}\n"
        output += f"Tamanho total: {total_size_mb:.2f} MB\n"
        output += f"Tempo médio de carregamento: {avg_load_time:.2f} ms\n"
        output += f"{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}\n"
        
        return output
        
    def generate_resource_list(self, output_format='text'):
        """
        Gera uma lista rápida com todas as imagens, CSS, JS e mídias carregadas
        Inclui caminho, tamanho e tempo de carregamento
        
        Args:
            output_format (str): Formato de saída ('text' ou 'csv')
        
        Returns:
            str: Caminho do arquivo gerado ou texto da lista
        """
        print(f"{Fore.YELLOW}Gerando lista de recursos...")
        
        # Cabeçalhos para a lista
        headers = ['Tipo', 'URL', 'Tamanho (KB)', 'Tempo (s)', 'Tempo (ms)', 'Status']
        
        # Preparar dados de todos os recursos
        resource_data = []
        
        # Adicionar página HTML principal
        html_load_time_s = round(self.total_load_time, 2)
        html_load_time_ms = round(self.total_load_time * 1000, 2)
        resource_data.append([
            'HTML', self.url, round(self.page_size / 1024, 2), 
            html_load_time_s, html_load_time_ms, '200'
        ])
        
        # Adicionar todos os outros recursos
        for resource_type, resources in self.resources.items():
            for resource in resources:
                load_time_s = round(resource.get('load_time', 0), 2)
                load_time_ms = round(resource.get('load_time', 0) * 1000, 2)
                resource_data.append([
                    resource_type,
                    resource.get('url', 'N/A'),
                    round(resource.get('size', 0) / 1024, 2),
                    load_time_s,
                    load_time_ms,
                    str(resource.get('status_code', 'N/A'))
                ])
        
        # Ordenar por tipo e depois por tempo de carregamento (decrescente)
        resource_data.sort(key=lambda x: (x[0], -x[3]))
        
        if output_format == 'csv':
            # Criar nome de arquivo
            domain = self.domain.replace(".", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{self.output_dir}/resource_list_{domain}_{timestamp}.csv"
            
            # Garantir que o diretório existe
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Escrever no arquivo CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(resource_data)
            
            print(f"{Fore.GREEN}Lista de recursos gerada em: {output_file}")
            return output_file
        else:
            # Gerar saída de texto formatada
            output_text = f"\n{'=' * 80}\n"
            output_text += f"LISTA DE RECURSOS CARREGADOS: {self.url}\n"
            output_text += f"{'=' * 80}\n\n"
            
            # Calcular larguras de coluna
            type_width = max(len('Tipo'), max(len(row[0]) for row in resource_data))
            url_width = min(70, max(len('URL'), max(len(row[1]) for row in resource_data)))
            size_width = max(len('Tamanho (KB)'), max(len(str(row[2])) for row in resource_data))
            time_s_width = max(len('Tempo (s)'), max(len(str(row[3])) for row in resource_data))
            time_ms_width = max(len('Tempo (ms)'), max(len(str(row[4])) for row in resource_data))
            status_width = max(len('Status'), max(len(str(row[5])) for row in resource_data))
            
            # Criar cabeçalho da tabela
            header_format = f"{{:<{type_width}}}  {{:<{url_width}}}  {{:>{size_width}}}  {{:>{time_s_width}}}  {{:>{time_ms_width}}}  {{:>{status_width}}}\n"
            output_text += header_format.format(*headers)
            output_text += "-" * (type_width + url_width + size_width + time_s_width + time_ms_width + status_width + 25) + "\n"
            
            # Adicionar linhas de dados
            row_format = f"{{:<{type_width}}}  {{:<{url_width}}}  {{:>{size_width}.2f}}  {{:>{time_s_width}.2f}}  {{:>{time_ms_width}.2f}}  {{:>{status_width}}}\n"
            
            # Agrupar por tipo de recurso
            current_type = ""
            for row in resource_data:
                if row[0] != current_type:
                    current_type = row[0]
                    output_text += f"\n{current_type.upper()}:\n"
                
                # Truncar URL se necessário
                url = row[1]
                if len(url) > url_width:
                    url = "..." + url[-(url_width-3):]
                
                output_text += row_format.format(
                    "", url, row[2], row[3], row[4], row[5]
                )
            
            return output_text

    def _generate_graphs(self, timestamp, domain):
        """
        Gera gráficos de análise
        """
        print(f"{Fore.YELLOW}Gerando gráficos de análise...")
        
        try:
            # Gráfico de tempo de carregamento por tipo de recurso
            self._generate_load_time_graph(timestamp, domain)
            
            # Gráfico de distribuição de status HTTP
            self._generate_status_codes_graph(timestamp, domain)
            
            # Gráfico de distribuição de tamanho por tipo
            self._generate_size_distribution_graph(timestamp, domain)
            
            print(f"{Fore.GREEN}Gráficos gerados com sucesso no diretório: {self.graphs_dir}")
        
        except Exception as e:
            print(f"{Fore.RED}Erro ao gerar gráficos: {e}")
    
    def _generate_load_time_graph(self, timestamp, domain):
        """
        Gera gráfico de tempo de carregamento por tipo de recurso
        """
        plt.figure(figsize=(12, 6))
        
        # Coletar dados para o gráfico
        resource_types = []
        avg_times = []
        max_times = []
        
        for resource_type, resources in self.resources.items():
            if resources:
                resource_types.append(resource_type)
                times = [resource.get('load_time', 0) for resource in resources]
                avg_times.append(sum(times) / len(times))
                max_times.append(max(times))
        
        # API tempos
        api_types = []
        api_avg_times = []
        api_max_times = []
        
        for api_type, apis in self.apis.items():
            if apis:
                analyzed_apis = [api for api in apis if api.get('analyzed', False)]
                if analyzed_apis:
                    api_types.append(api_type)
                    times = [api.get('load_time', 0) for api in analyzed_apis]
                    api_avg_times.append(sum(times) / len(times))
                    api_max_times.append(max(times))
        
        # Cores Material Design
        colors = {
            'primary': '#1976D2',   # Azul
            'secondary': '#FF5722', # Laranja
            'success': '#4CAF50',   # Verde
            'warning': '#FFC107',   # Amarelo
            'error': '#F44336'      # Vermelho
        }
        
        # Gráfico para recursos
        x = range(len(resource_types))
        plt.bar(x, avg_times, width=0.4, label='Tempo Médio', color=colors['primary'], alpha=0.7)
        plt.bar([i + 0.4 for i in x], max_times, width=0.4, label='Tempo Máximo', color=colors['error'], alpha=0.7)
        
        plt.xlabel('Tipo de Recurso')
        plt.ylabel('Tempo (segundos)')
        plt.title('Tempo de Carregamento por Tipo de Recurso')
        plt.xticks([i + 0.2 for i in x], resource_types)
        plt.legend()
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Salvar o gráfico como arquivo e em base64
        file_path = f"{self.graphs_dir}/load_times_{domain}_{timestamp}.png"
        plt.savefig(file_path, dpi=100)
        self.graph_images['load_times'] = self._fig_to_base64(plt.gcf())
        plt.close()
        
        # Gráfico para APIs se houver dados
        if api_types:
            plt.figure(figsize=(12, 6))
            x = range(len(api_types))
            plt.bar(x, api_avg_times, width=0.4, label='Tempo Médio', color=colors['success'], alpha=0.7)
            plt.bar([i + 0.4 for i in x], api_max_times, width=0.4, label='Tempo Máximo', color=colors['warning'], alpha=0.7)
            
            plt.xlabel('Tipo de API')
            plt.ylabel('Tempo (segundos)')
            plt.title('Tempo de Carregamento por Tipo de API')
            plt.xticks([i + 0.2 for i in x], api_types)
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            # Salvar o gráfico como arquivo e em base64
            file_path = f"{self.graphs_dir}/api_load_times_{domain}_{timestamp}.png"
            plt.savefig(file_path, dpi=100)
            self.graph_images['api_load_times'] = self._fig_to_base64(plt.gcf())
            plt.close()
    
    def _fig_to_base64(self, fig):
        """
        Converte um matplotlib figure para uma string base64
        """
        import io
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        return img_str
    
    def _generate_status_codes_graph(self, timestamp, domain):
        """
        Gera gráfico de distribuição de códigos de status HTTP
        """
        if not self.http_stats['status_codes']:
            return
        
        plt.figure(figsize=(10, 6))
        
        status_codes = list(self.http_stats['status_codes'].keys())
        counts = list(self.http_stats['status_codes'].values())
        
        # Definir cores Material Design com base nas faixas de status
        colors = ['#4CAF50' if code == 200 else      # Verde para 200
                 '#2196F3' if 200 <= code < 300 else # Azul para 2xx
                 '#FF9800' if 300 <= code < 400 else # Laranja para 3xx
                 '#F44336' if 400 <= code < 500 else # Vermelho para 4xx
                 '#9C27B0' if 500 <= code < 600 else # Roxo para 5xx
                 '#9E9E9E' for code in status_codes] # Cinza para outros
        
        plt.bar(status_codes, counts, color=colors)
        
        plt.xlabel('Código de Status HTTP')
        plt.ylabel('Número de Requisições')
        plt.title('Distribuição de Códigos de Status HTTP')
        plt.xticks(status_codes)
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        
        # Adicionar rótulos de contagem acima das barras
        for i, count in enumerate(counts):
            plt.text(status_codes[i], count + 0.1, str(count), ha='center')
        
        plt.tight_layout()
        
        # Salvar o gráfico como arquivo e em base64
        file_path = f"{self.graphs_dir}/status_codes_{domain}_{timestamp}.png"
        plt.savefig(file_path, dpi=100)
        self.graph_images['status_codes'] = self._fig_to_base64(plt.gcf())
        plt.close()
    
    def _generate_size_distribution_graph(self, timestamp, domain):
        """
        Gera gráfico de distribuição de tamanho por tipo de recurso
        """
        plt.figure(figsize=(10, 6))
        
        # Coletar dados para o gráfico
        resource_types = []
        total_sizes_kb = []
        
        for resource_type, resources in self.resources.items():
            if resources:
                resource_types.append(resource_type)
                total_size = sum(resource.get('size', 0) for resource in resources) / 1024  # em KB
                total_sizes_kb.append(total_size)
        
        # Cores Material Design para o gráfico de pizza
        colors = ['#2196F3', '#4CAF50', '#FFC107', '#F44336', '#9C27B0', '#FF5722']
        
        # Gráfico de pizza
        plt.pie(total_sizes_kb, labels=resource_types, autopct='%1.1f%%',
               shadow=True, startangle=140, explode=[0.05] * len(resource_types),
               colors=colors[:len(resource_types)])
        
        plt.axis('equal')
        plt.title('Distribuição de Tamanho por Tipo de Recurso (KB)')
        plt.tight_layout()
        
        # Salvar o gráfico como arquivo e em base64
        file_path = f"{self.graphs_dir}/size_distribution_{domain}_{timestamp}.png"
        plt.savefig(file_path, dpi=100)
        self.graph_images['size_distribution'] = self._fig_to_base64(plt.gcf())
        plt.close()
        
        # Criar um gráfico de barras para os tempos médios de resposta
        plt.figure(figsize=(10, 6))
        
        resource_types_with_times = []
        avg_response_times = []
        
        for resource_type, resources in self.resources.items():
            if resources:
                resource_types_with_times.append(resource_type)
                times = [resource.get('time_to_first_byte', 0) for resource in resources if resource.get('time_to_first_byte')]
                if times:
                    avg_response_times.append(sum(times) / len(times))
                else:
                    avg_response_times.append(0)
        
        plt.bar(resource_types_with_times, avg_response_times, color='#673AB7')
        plt.xlabel('Tipo de Recurso')
        plt.ylabel('Tempo até o Primeiro Byte (s)')
        plt.title('Tempo Médio de Resposta (TTFB) por Tipo de Recurso')
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        plt.tight_layout()
        
        # Salvar o gráfico como arquivo e em base64
        file_path = f"{self.graphs_dir}/ttfb_distribution_{domain}_{timestamp}.png"
        plt.savefig(file_path, dpi=100)
        self.graph_images['ttfb_distribution'] = self._fig_to_base64(plt.gcf())
        plt.close()

    def print_summary(self):
        """
        Imprime um resumo da análise
        """
        total_resources = sum(len(resources) for resources in self.resources.values())
        total_size = self.page_size + sum(
            resource.get('size', 0) for resource_type in self.resources.values() 
            for resource in resource_type
        )
        
        # Contagem total de APIs analisadas
        total_apis = sum(len([api for api in apis if api.get('analyzed', False)]) for apis in self.apis.values())
        
        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.CYAN}RESUMO DA ANÁLISE")
        print(f"{Fore.CYAN}{'=' * 70}")
        print(f"URL analisada: {self.url}")
        print(f"Total de recursos: {total_resources}")
        print(f"Total de possíveis APIs/endpoints: {total_apis}")
        print(f"Tamanho total da página: {total_size/1024/1024:.2f} MB")
        print(f"Tempo total de carregamento: {self.total_load_time:.2f} segundos")
        
        # Resumo HTTP
        print(f"\n{Fore.MAGENTA}ESTATÍSTICAS HTTP:")
        print(f"  Total de requisições: {self.http_stats['total_requests']}")
        print(f"  Requisições com falha: {self.http_stats['failed_requests']}")
        
        # Tempos de resposta
        if self.http_stats['response_times']:
            print(f"  Tempo médio de resposta: {statistics.mean(self.http_stats['response_times']):.3f}s")
            print(f"  Tempo mínimo de resposta: {min(self.http_stats['response_times']):.3f}s")
            print(f"  Tempo máximo de resposta: {max(self.http_stats['response_times']):.3f}s")
            if len(self.http_stats['response_times']) > 1:
                print(f"  Desvio padrão: {statistics.stdev(self.http_stats['response_times']):.3f}s")
        
        # Distribuição de códigos de status
        print(f"\n{Fore.MAGENTA}CÓDIGOS DE STATUS HTTP:")
        for status, count in sorted(self.http_stats['status_codes'].items()):
            status_color = Fore.GREEN if status == 200 else (
                           Fore.BLUE if 200 <= status < 300 else (
                           Fore.YELLOW if 300 <= status < 400 else (
                           Fore.RED if 400 <= status < 500 else Fore.RED)))
            print(f"  {status_color}Status {status}: {count} requisições")
        
        # Top 5 tipos de conteúdo
        content_types = sorted(self.http_stats['content_types'].items(), key=lambda x: x[1], reverse=True)[:5]
        if content_types:
            print(f"\n{Fore.MAGENTA}TOP 5 TIPOS DE CONTEÚDO:")
            for content_type, count in content_types:
                print(f"  {content_type}: {count} recursos")
        
        # Estatísticas por tipo de recurso
        print(f"\n{Fore.CYAN}DETALHES POR TIPO DE RECURSO:")
        for resource_type, resources in self.resources.items():
            if resources:
                type_size = sum(resource.get('size', 0) for resource in resources)
                type_time = sum(resource.get('load_time', 0) for resource in resources)
                print(f"\n{Fore.YELLOW}{resource_type.upper()}:")
                print(f"  Quantidade: {len(resources)}")
                print(f"  Tamanho total: {type_size/1024:.2f} KB")
                print(f"  Tempo médio de carregamento: {type_time/len(resources):.2f} segundos")
                
                # Estatísticas específicas para cada tipo de recurso
                if resource_type == 'images' and resources:
                    # Calcular tamanho médio de imagens
                    avg_img_size = type_size / len(resources) / 1024  # em KB
                    print(f"  Tamanho médio das imagens: {avg_img_size:.2f} KB")
                    
                    # Contar imagens por formato
                    formats = {}
                    for img in resources:
                        fmt = img.get('img_format', 'Unknown')
                        formats[fmt] = formats.get(fmt, 0) + 1
                    
                    print(f"  Formatos de imagens:")
                    for fmt, count in formats.items():
                        if fmt != 'Unknown':
                            print(f"    - {fmt}: {count}")
                    
                    # Imagens sem texto alternativo
                    no_alt = sum(1 for img in resources if not img.get('alt_text'))
                    if no_alt > 0:
                        print(f"  {Fore.RED}Imagens sem texto alternativo: {no_alt} ({no_alt/len(resources)*100:.1f}%)")
                
                elif resource_type == 'js':
                    # Contar scripts async/defer
                    async_scripts = sum(1 for js in resources if js.get('async') == 'async')
                    defer_scripts = sum(1 for js in resources if js.get('defer') == 'defer')
                    
                    if async_scripts > 0:
                        print(f"  Scripts assíncronos: {async_scripts} ({async_scripts/len(resources)*100:.1f}%)")
                    if defer_scripts > 0:
                        print(f"  Scripts com defer: {defer_scripts} ({defer_scripts/len(resources)*100:.1f}%)")
        
        # Resumo de APIs detectadas
        if total_apis > 0:
            print(f"\n{Fore.CYAN}APIS E ENDPOINTS DETECTADOS:")
            for api_type, apis in self.apis.items():
                analyzed_apis = [api for api in apis if api.get('analyzed', False)]
                if analyzed_apis:
                    avg_time = sum(api.get('load_time', 0) for api in analyzed_apis) / len(analyzed_apis)
                    print(f"\n{Fore.YELLOW}{api_type.upper()}:")
                    print(f"  Quantidade: {len(analyzed_apis)}")
                    print(f"  Tempo médio de resposta: {avg_time:.3f} segundos")
                    
                    # Listar URLs das APIs (limitado a 5 para não sobrecarregar o console)
                    if len(analyzed_apis) <= 5:
                        for api in analyzed_apis:
                            status = api.get('status_code', 0)
                            status_color = Fore.GREEN if status == 200 else (
                                           Fore.YELLOW if 300 <= status < 400 else Fore.RED)
                            print(f"  - {status_color}{api['url']} ({status})")
                    else:
                        print(f"  {len(analyzed_apis)} endpoints encontrados. Veja o relatório para detalhes.")
        
        # Estatísticas de cache
        cached_resources = sum(1 for resource_type in self.resources.values() 
                              for resource in resource_type 
                              if 'max-age' in resource.get('cache_control', ''))
        
        # Estatísticas de compressão
        compressed_resources = sum(1 for resource_type in self.resources.values() 
                                  for resource in resource_type 
                                  if resource.get('content_encoding') not in ['none', None, ''])
        
        print(f"\n{Fore.CYAN}OTIMIZAÇÃO DO SITE:")
        if cached_resources > 0:
            cached_percent = cached_resources / total_resources * 100
            print(f"{Fore.GREEN}Recursos com cache configurado: {cached_resources} ({cached_percent:.1f}%)")
        
        if compressed_resources > 0:
            compressed_percent = compressed_resources / total_resources * 100
            print(f"{Fore.GREEN}Recursos comprimidos: {compressed_resources} ({compressed_percent:.1f}%)")
        
        # Tempos médios de carregamento
        if self.http_stats['response_times']:
            slow_resources = sum(1 for resource_type in self.resources.values() 
                                for resource in resource_type 
                                if resource.get('load_time', 0) > 0.5)
            
            if slow_resources > 0:
                slow_percent = slow_resources / total_resources * 100
                print(f"{Fore.YELLOW}Recursos lentos (>0.5s): {slow_resources} ({slow_percent:.1f}%)")
        
        print(f"\n{Fore.CYAN}{'=' * 70}\n")


def main():
    """
    Função principal
    """
    parser = argparse.ArgumentParser(description='Analisador de Performance de Websites')
    parser.add_argument('--url', required=True, help='URL do site a ser analisado')
    parser.add_argument('--output', default='reports', help='Diretório para salvar relatórios (padrão: reports)')
    parser.add_argument('--detail-level', choices=['basic', 'full'], default='full', 
                        help='Nível de detalhe das métricas (basic: métricas básicas, full: todas as métricas)')
    parser.add_argument('--timeout', type=int, default=30, 
                        help='Timeout em segundos para requisições (padrão: 30)')
    parser.add_argument('--user-agent', default=None, 
                        help='User-Agent personalizado para as requisições')
    parser.add_argument('--no-html', action='store_true',
                        help='Desativa a geração de relatório HTML')
    parser.add_argument('--list-resources', action='store_true',
                        help='Exibe uma lista rápida com todas as imagens, CSS, JS, e mídias carregadas')
    parser.add_argument('--list-format', choices=['text', 'csv'], default='text',
                        help='Formato da lista de recursos (text: exibe no terminal, csv: salva em arquivo)')
    parser.add_argument('--assets-table', action='store_true',
                        help='Exibe uma tabela completa com todos os assets, tamanhos em KB e tempos em ms')
    
    args = parser.parse_args()
    
    print(f"{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}{'ANALISADOR DE PERFORMANCE DE WEBSITES':^70}")
    print(f"{Fore.CYAN}{'=' * 70}")
    
    tester = WebsitePerformanceTester(args.url, args.output)
    
    # Configurar timeout personalizado se especificado
    if args.timeout != 30:
        tester.session.timeout = args.timeout
        
    # Configurar User-Agent personalizado se especificado
    if args.user_agent:
        tester.session.headers.update({'User-Agent': args.user_agent})
    
    tester.analyze_website()
    
    # Gerar lista rápida de recursos se solicitado
    if args.list_resources:
        resource_list = tester.generate_resource_list(args.list_format)
        if args.list_format == 'text':
            print(resource_list)
    
    # Gerar tabela completa de assets se solicitado
    if args.assets_table:
        assets_table = tester.generate_assets_table()
        print(assets_table)
    
    # Gerar relatório completo
    csv_report, html_report = tester.generate_report()
    
    # Exibir resumo se não estiver no modo de lista de recursos ou tabela de assets
    if (not args.list_resources or args.list_format == 'csv') and not args.assets_table:
        tester.print_summary()
    
    # URL já está processada pela classe, não precisamos gerar nome novamente
    
    print(f"{Fore.GREEN}Análise completa! Relatórios salvos.")
    print(f"{Fore.GREEN}Relatório CSV: {csv_report}")
    print(f"{Fore.GREEN}Relatório HTML: {html_report}")
    
    # Sugerir abrir o relatório HTML
    if os.path.exists(html_report):
        print(f"\n{Fore.CYAN}Para visualizar o relatório HTML completo com gráficos, execute:")
        print(f"{Fore.YELLOW}open {html_report}")
        
        # Abrir automaticamente o relatório HTML no navegador padrão
        if not args.no_html:
            try:
                print(f"\n{Fore.CYAN}Abrindo relatório HTML no navegador padrão...")
                html_absolute_path = os.path.abspath(html_report)
                webbrowser.open(f"file://{html_absolute_path}")
            except Exception as e:
                print(f"{Fore.YELLOW}Não foi possível abrir o navegador: {str(e)}")
                pass


if __name__ == "__main__":
    main()
