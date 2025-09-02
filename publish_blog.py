#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para publicar o post do blog pyFormanceTester em várias plataformas.
Suporta Medium, Dev.to, LinkedIn e Hashnode.
"""

import os
import sys
import json
import argparse
import requests
import markdown
import html2text
from pathlib import Path

# Cores para saída no terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def load_config(config_path="publish_config.json"):
    """Carrega as configurações de API das plataformas"""
    if not os.path.exists(config_path):
        print(f"{Colors.RED}Erro: Arquivo de configuração {config_path} não encontrado.{Colors.END}")
        print(f"Crie um arquivo {config_path} com o seguinte formato:")
        print("""
{
    "medium": {
        "token": "seu-token-medium",
        "publication_id": "id-da-publicacao-opcional"
    },
    "devto": {
        "api_key": "sua-chave-api-devto"
    },
    "hashnode": {
        "api_key": "sua-chave-api-hashnode",
        "publication_id": "id-da-publicacao"
    },
    "linkedin": {
        "access_token": "seu-token-linkedin",
        "author_id": "seu-id-linkedin"
    }
}
        """)
        return None
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Colors.RED}Erro ao carregar configurações: {str(e)}{Colors.END}")
        return None

def read_markdown_post(file_path="BLOG_POST.md"):
    """Lê o arquivo markdown do post"""
    if not os.path.exists(file_path):
        print(f"{Colors.RED}Erro: Arquivo do post {file_path} não encontrado.{Colors.END}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"{Colors.RED}Erro ao ler o arquivo do post: {str(e)}{Colors.END}")
        return None

def convert_markdown_to_html(markdown_text):
    """Converte markdown para HTML"""
    import markdown
    return markdown.markdown(
        markdown_text, 
        extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.tables',
            'markdown.extensions.toc'
        ]
    )

def publish_to_medium(token, content, title, tags, publication_id=None):
    """Publica no Medium"""
    url = "https://api.medium.com/v1/users/me/posts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Se houver ID de publicação, use-o
    if publication_id:
        data = {
            "title": title,
            "contentFormat": "markdown",
            "content": content,
            "tags": tags,
            "publishStatus": "draft",
            "publicationId": publication_id
        }
    else:
        data = {
            "title": title,
            "contentFormat": "markdown",
            "content": content,
            "tags": tags,
            "publishStatus": "draft"
        }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            post_data = response.json()
            return True, post_data.get('data', {}).get('url', 'URL não disponível')
        else:
            return False, f"Erro {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def publish_to_devto(api_key, content, title, tags):
    """Publica no Dev.to"""
    url = "https://dev.to/api/articles"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    data = {
        "article": {
            "title": title,
            "body_markdown": content,
            "published": False,
            "tags": tags
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            post_data = response.json()
            return True, post_data.get('url', 'URL não disponível')
        else:
            return False, f"Erro {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def publish_to_hashnode(api_key, publication_id, content, title, tags):
    """Publica no Hashnode usando a API GraphQL"""
    url = "https://api.hashnode.com/"
    
    # GraphQL mutation para publicação
    query = """
    mutation createPublicationStory(
        $publicationId: String!,
        $title: String!,
        $contentMarkdown: String!,
        $tags: [TagsInput]!
    ) {
        createPublicationStory(
            publicationId: $publicationId,
            input: {
                title: $title,
                contentMarkdown: $contentMarkdown,
                tags: $tags,
                isRepublished: {originalArticleURL: ""}
            }
        ) {
            code
            success
            message
            post {
                slug
                title
            }
        }
    }
    """
    
    # Formatar as tags
    formatted_tags = [{"_id": tag, "slug": tag.lower()} for tag in tags]
    
    variables = {
        "publicationId": publication_id,
        "title": title,
        "contentMarkdown": content,
        "tags": formatted_tags
    }
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json={"query": query, "variables": variables}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data', {}).get('createPublicationStory', {}).get('success'):
                post = data['data']['createPublicationStory']['post']
                return True, f"Post criado: {post['slug']}"
            else:
                message = data.get('data', {}).get('createPublicationStory', {}).get('message', 'Erro desconhecido')
                return False, message
        else:
            return False, f"Erro {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def publish_to_linkedin(access_token, author_id, content, title):
    """Publica no LinkedIn"""
    url = f"https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    # Converter para texto puro (LinkedIn não aceita markdown diretamente)
    h = html2text.HTML2Text()
    h.ignore_links = False
    text = h.handle(convert_markdown_to_html(content))
    
    # Limitar o tamanho para a API do LinkedIn
    if len(text) > 3000:
        text = text[:2997] + "..."
    
    data = {
        "author": f"urn:li:person:{author_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": f"{title}\n\n{text[:1000]}..."
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            post_data = response.json()
            return True, "Post publicado no LinkedIn"
        else:
            return False, f"Erro {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(description='Publicador de posts para diversas plataformas')
    parser.add_argument('--file', default='BLOG_POST.md', help='Arquivo markdown do post')
    parser.add_argument('--config', default='publish_config.json', help='Arquivo de configuração')
    parser.add_argument('--title', default='pyFormanceTester: Uma Ferramenta Avançada para Análise de Performance de Websites', 
                        help='Título do post')
    parser.add_argument('--tags', default='python,performance,web,tools,seo', 
                        help='Tags separadas por vírgula')
    parser.add_argument('--platforms', default='all', 
                        help='Plataformas para publicar (separadas por vírgula): medium,devto,hashnode,linkedin ou "all"')
    
    args = parser.parse_args()
    
    # Converter tags para lista
    tags = [tag.strip() for tag in args.tags.split(',')]
    
    # Determinar quais plataformas usar
    if args.platforms.lower() == 'all':
        platforms = ['medium', 'devto', 'hashnode', 'linkedin']
    else:
        platforms = [p.strip().lower() for p in args.platforms.split(',')]
    
    # Carregar configurações
    config = load_config(args.config)
    if not config:
        return
    
    # Ler o post
    content = read_markdown_post(args.file)
    if not content:
        return
    
    print(f"{Colors.BOLD}Publicando post: {args.title}{Colors.END}")
    print(f"Tags: {', '.join(tags)}")
    print(f"Plataformas: {', '.join(platforms)}")
    print("-" * 50)
    
    # Publicar em cada plataforma selecionada
    if 'medium' in platforms and 'medium' in config:
        print(f"{Colors.YELLOW}Publicando no Medium...{Colors.END}")
        success, message = publish_to_medium(
            config['medium']['token'], 
            content, 
            args.title, 
            tags,
            config['medium'].get('publication_id')
        )
        
        if success:
            print(f"{Colors.GREEN}✓ Post publicado no Medium: {message}{Colors.END}")
        else:
            print(f"{Colors.RED}✗ Falha ao publicar no Medium: {message}{Colors.END}")
    
    if 'devto' in platforms and 'devto' in config:
        print(f"{Colors.YELLOW}Publicando no Dev.to...{Colors.END}")
        success, message = publish_to_devto(
            config['devto']['api_key'],
            content,
            args.title,
            tags[:4]  # Dev.to limita a 4 tags
        )
        
        if success:
            print(f"{Colors.GREEN}✓ Post publicado no Dev.to: {message}{Colors.END}")
        else:
            print(f"{Colors.RED}✗ Falha ao publicar no Dev.to: {message}{Colors.END}")
    
    if 'hashnode' in platforms and 'hashnode' in config:
        print(f"{Colors.YELLOW}Publicando no Hashnode...{Colors.END}")
        success, message = publish_to_hashnode(
            config['hashnode']['api_key'],
            config['hashnode']['publication_id'],
            content,
            args.title,
            tags
        )
        
        if success:
            print(f"{Colors.GREEN}✓ Post publicado no Hashnode: {message}{Colors.END}")
        else:
            print(f"{Colors.RED}✗ Falha ao publicar no Hashnode: {message}{Colors.END}")
    
    if 'linkedin' in platforms and 'linkedin' in config:
        print(f"{Colors.YELLOW}Publicando no LinkedIn...{Colors.END}")
        success, message = publish_to_linkedin(
            config['linkedin']['access_token'],
            config['linkedin']['author_id'],
            content,
            args.title
        )
        
        if success:
            print(f"{Colors.GREEN}✓ Post publicado no LinkedIn: {message}{Colors.END}")
        else:
            print(f"{Colors.RED}✗ Falha ao publicar no LinkedIn: {message}{Colors.END}")
    
    print("-" * 50)
    print(f"{Colors.GREEN}Processo de publicação concluído!{Colors.END}")

if __name__ == "__main__":
    main()
