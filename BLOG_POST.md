# pyFormanceTester: Uma Ferramenta Avançada para Análise de Performance de Websites

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)

![pyFormanceTester Banner](https://i.imgur.com/zLXTS8i.jpg)

Em um mundo onde a velocidade de carregamento de um website pode significar a diferença entre engajar um usuário ou perdê-lo para a concorrência, ferramentas de análise de performance se tornaram essenciais para desenvolvedores web e profissionais de SEO. É nesse contexto que desenvolvi o **pyFormanceTester**, uma solução completa para análise detalhada da performance de websites.

## Por que criei o pyFormanceTester?

As ferramentas existentes para análise de performance, como o Google Lighthouse e o WebPageTest, são excelentes, mas muitas vezes não oferecem o nível de granularidade e flexibilidade que precisamos para projetos específicos. Além disso, integrar essas ferramentas em fluxos de trabalho automatizados nem sempre é trivial.

O pyFormanceTester nasceu da necessidade de:

1. **Analisar recursos individuais** de um site com grande detalhamento
2. **Detectar automaticamente APIs** em aplicações web modernas
3. **Gerar relatórios customizáveis** em múltiplos formatos
4. **Integrar facilmente** com pipelines de CI/CD e fluxos de trabalho de desenvolvimento

## O que o pyFormanceTester faz?

Em sua essência, o pyFormanceTester é uma ferramenta de linha de comando em Python que analisa completamente um website, coletando métricas sobre cada recurso carregado e gerando relatórios detalhados. Suas principais funcionalidades incluem:

### 1. Análise Completa de Recursos

O pyFormanceTester não apenas verifica o HTML principal, mas rastreia e analisa **todos os recursos** carregados:

- **Imagens**: JPG, PNG, WebP, SVG, GIF, etc.
- **Scripts**: JavaScript interno e externo
- **Estilos**: CSS interno e externo
- **Fontes**: Webfonts como WOFF, WOFF2, TTF
- **Mídia**: Vídeos, áudio e outros arquivos multimídia
- **APIs**: Chamadas de API e requisições AJAX

Para cada recurso, são coletadas informações como:

- Tamanho em bytes/KB
- Tempo de carregamento
- Tipo MIME
- Cabeçalhos HTTP (incluindo cache, compressão)
- Métricas específicas por tipo (dimensões de imagens, scripts async/defer, etc.)

### 2. Detecção Avançada de APIs

Uma característica distintiva do pyFormanceTester é sua capacidade de **detectar APIs** em websites modernos. Utilizando técnicas sofisticadas de análise, ele identifica:

- Chamadas XMLHttpRequest (XHR)
- Requisições usando a Fetch API
- Endpoints JSON e RESTful
- Chamadas GraphQL
- APIs específicas de e-commerce (produtos, catálogos, etc.)

Esta funcionalidade é particularmente útil para desenvolvedores que precisam mapear APIs em aplicações web complexas ou para equipes de segurança realizando auditorias.

### 3. Relatórios Ricos e Customizáveis

O pyFormanceTester gera relatórios em múltiplos formatos para atender diferentes necessidades:

- **Relatórios CSV**: Dados brutos para análise posterior ou integração com outras ferramentas
- **Relatórios HTML**: Interface visual elegante com Material Design
- **Gráficos interativos**: Visualizações que facilitam a compreensão dos dados
- **Tabelas coloridas no terminal**: Para análises rápidas sem sair do ambiente de desenvolvimento

O relatório HTML merece destaque especial por sua interface limpa e intuitiva, que apresenta:

- Resumo geral do site
- Distribuição de recursos por tipo
- Gráficos de tamanho vs. tempo de carregamento
- Lista dos recursos mais pesados e mais lentos
- Recomendações automáticas de otimização

E o melhor de tudo: o tema da interface pode ser personalizado entre claro e escuro através do arquivo de configuração!

#### Tema Claro e Escuro

![Tema Claro](https://i.imgur.com/IkN0Bsd.jpg)
![Tema Escuro](https://i.imgur.com/RZDvF4N.jpg)

O usuário pode alternar facilmente entre os temas claro e escuro ajustando uma simples configuração no arquivo `config.json`.

### 4. Configuração Flexível

O pyFormanceTester oferece diversas opções de configuração, permitindo adaptá-lo a diferentes necessidades:

- **Timeout personalizado**: Para sites mais lentos ou conexões limitadas
- **User-Agent customizado**: Permite simular diferentes dispositivos
- **Níveis de detalhe**: Análise básica ou completa
- **Formatos de saída**: CSV, HTML, texto no terminal
- **Temas de interface**: Claro ou escuro

## Como usar o pyFormanceTester

Usar a ferramenta é extremamente simples:

```bash
# Análise básica
python _test.py --url https://www.exemplo.com.br

# Listar apenas os recursos
python _test.py --url https://www.exemplo.com.br --list-resources

# Gerar tabela completa com todos os assets
python _test.py --url https://www.exemplo.com.br --assets-table

# Simular dispositivo móvel
python _test.py --url https://www.exemplo.com.br --user-agent "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
```

### Exemplos de Saídas

#### 1. Relatório HTML Interativo

![Relatório HTML](https://i.imgur.com/LyHRRGv.jpg)

O relatório HTML gerado automaticamente apresenta uma visão geral da performance do site, incluindo métricas chave, gráficos e tabelas com recursos organizados.

#### 2. Tabela de Assets no Terminal

![Tabela de Assets](https://i.imgur.com/WxbQA4d.jpg)

Uma tabela colorida exibida diretamente no terminal, mostrando todos os recursos carregados com seus respectivos tamanhos e tempos de carregamento.

#### 3. Gráficos de Análise

![Gráfico de Distribuição de Tamanho](https://i.imgur.com/R7XSkVc.jpg)
![Gráfico de Tempo de Carregamento](https://i.imgur.com/F2lDAw2.jpg)

Gráficos gerados automaticamente mostram a distribuição de tamanho dos recursos e os tempos de carregamento, facilitando a identificação de possíveis problemas de performance.

## Casos de uso reais

O pyFormanceTester tem se mostrado valioso em diversos cenários:

### Otimização de Websites de E-commerce

Para um cliente de e-commerce, utilizamos o pyFormanceTester para identificar gargalos de performance que estavam aumentando a taxa de abandono do carrinho. A ferramenta revelou:

- Imagens não otimizadas consumindo mais de 70% do tamanho total da página
- APIs de preço e estoque muito lentas, impactando o tempo de carregamento do produto
- Scripts de terceiros bloqueando o renderização da página

Após as otimizações sugeridas pelo relatório, o site teve uma redução de 62% no tempo de carregamento e um aumento de 18% na taxa de conversão.

### Auditoria de APIs em Aplicações SPA

Para uma aplicação Angular complexa, o pyFormanceTester identificou mais de 30 endpoints de API não documentados, alguns expondo dados sensíveis sem a devida autenticação. O mapeamento automático dessas APIs permitiu à equipe de segurança corrigir vulnerabilidades críticas antes do lançamento.

### Monitoramento Contínuo em CI/CD

Integrado a um pipeline Jenkins, o pyFormanceTester passou a monitorar automaticamente a performance a cada deploy, alertando a equipe sempre que métricas chave ultrapassam limites predefinidos. Isso evitou que problemas de performance chegassem ao ambiente de produção.

## O que vem a seguir?

O pyFormanceTester continua evoluindo! Entre os próximos recursos planejados estão:

- **Integração com Lighthouse**: Combinar nossas métricas com as do Lighthouse para análises ainda mais abrangentes
- **Modo headless**: Captura de recursos carregados via JavaScript em SPAs usando navegador headless
- **Comparativo de versões**: Compare a performance antes e depois de alterações
- **Análise de Core Web Vitals**: Medição de LCP, FID, CLS e outras métricas de experiência do usuário
- **Dashboard em tempo real**: Monitoramento contínuo da performance de múltiplos sites

## Benefícios da Análise de Performance

O uso consistente de ferramentas como o pyFormanceTester pode trazer diversos benefícios:

1. **Redução do Tempo de Carregamento**: Identificando recursos problemáticos que podem ser otimizados
2. **Melhoria nas Taxas de Conversão**: Sites mais rápidos têm taxas de conversão significativamente melhores
3. **Economia de Largura de Banda**: Tanto para o servidor quanto para os usuários
4. **Melhor Posicionamento SEO**: A velocidade é um fator de ranqueamento importante
5. **Experiência do Usuário Aprimorada**: Especialmente em dispositivos móveis e conexões instáveis

## Conclusão

Em um mundo onde a performance web é cada vez mais crucial, o pyFormanceTester oferece uma visão detalhada e acionável sobre cada aspecto do seu website. Seja você um desenvolvedor web, um profissional de SEO ou um gestor de produto, esta ferramenta pode ajudar a identificar problemas, otimizar recursos e oferecer uma experiência melhor para seus usuários.

O código é aberto, e contribuições são bem-vindas! Sinta-se à vontade para experimentar, reportar bugs ou sugerir novos recursos.

![Diagrama de Funcionamento](https://i.imgur.com/8LdxfUv.jpg)

---

**Sobre o autor**: Allan Ramos (Jaccon) é desenvolvedor full-stack com mais de 15 anos de experiência, especializado em otimização de performance web e ferramentas de desenvolvimento.

---

*As imagens utilizadas neste post são meramente ilustrativas e representam exemplos de relatórios que podem ser gerados pela ferramenta. Os resultados reais podem variar dependendo do site analisado e das configurações utilizadas.*
