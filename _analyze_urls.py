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
