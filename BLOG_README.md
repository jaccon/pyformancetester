# Blog Post - pyFormanceTester

Este diretório contém um post de blog detalhado sobre o pyFormanceTester, explicando suas funcionalidades, casos de uso e benefícios.

## Arquivos

- `BLOG_POST.md`: Post de blog completo em formato Markdown
- `publish_blog.py`: Script para automatizar a publicação do post em diferentes plataformas
- `publish_config.example.json`: Exemplo de arquivo de configuração para as credenciais das plataformas

## Como Publicar o Post

1. Primeiro, instale as dependências necessárias:

```bash
pip install requests markdown html2text
```

2. Crie um arquivo `publish_config.json` baseado no exemplo fornecido:

```bash
cp publish_config.example.json publish_config.json
```

3. Edite o arquivo `publish_config.json` e adicione suas credenciais para cada plataforma.

4. Execute o script de publicação:

```bash
# Publicar em todas as plataformas configuradas
python publish_blog.py

# Publicar apenas em plataformas específicas
python publish_blog.py --platforms medium,devto

# Usar um arquivo diferente ou título personalizado
python publish_blog.py --file my_post.md --title "Meu Título Personalizado" --tags "python,ferramentas,webdev"
```

## Obtenção de Tokens de API

### Medium
1. Acesse https://medium.com/me/settings
2. Vá para "Integration tokens"
3. Crie um novo token

### Dev.to
1. Acesse https://dev.to/settings/account
2. Vá para "DEV Community API Keys"
3. Gere uma nova chave de API

### Hashnode
1. Acesse https://hashnode.com/settings/developer
2. Crie um novo token pessoal

### LinkedIn
O processo para o LinkedIn é mais complexo e requer a criação de um aplicativo no LinkedIn Developer Portal. Consulte a documentação oficial para mais detalhes.

## Personalização do Post

Sinta-se à vontade para personalizar o post antes de publicá-lo:

- Adicione ou altere imagens
- Ajuste o conteúdo para seu público específico
- Altere os exemplos ou casos de uso
- Atualize os dados de acordo com seus próprios testes

## Observações

- Os posts são publicados como rascunhos nas plataformas que suportam esse recurso
- Lembre-se de revisar o conteúdo em cada plataforma antes de publicá-lo oficialmente
- Algumas plataformas podem ter limitações quanto ao número de imagens ou formatação
