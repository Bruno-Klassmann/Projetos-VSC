# Assistente de Compras - Comparador de Preços

## 📋 Visão Geral

O Assistente de Compras é uma aplicação web que busca e compara preços de produtos no Google Shopping, apresentando as 3 melhores ofertas encontradas. Desenvolvido para facilitar a busca por melhores preços online, o assistente permite exportar os resultados em formato Excel, incluindo links diretos para os carrinhos de compras.

## ✨ Funcionalidades

- **Busca no Google Shopping**: Encontra produtos usando a API SerpApi para resultados confiáveis
- **Top 3 Melhores Ofertas**: Apresenta as três ofertas com melhor preço, ordenadas automaticamente
- **Exportação para Excel**: Gera planilhas XLSX com informações detalhadas dos produtos e links diretos
- **Interface Responsiva**: Design moderno que funciona em dispositivos móveis e desktop
- **Histórico de Buscas**: Mantém registro das pesquisas anteriores para fácil acesso

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python com Flask
- **Frontend**: HTML5, CSS3, JavaScript moderno
- **Integração**: SerpApi para busca confiável no Google Shopping
- **Exportação de Dados**: Pandas e OpenPyXL para geração de planilhas
- **Estilização**: CSS personalizado com design responsivo

## 📦 Instalação

1. Clone este repositório:
   ```bash
   git clone https://github.com/seu-usuario/assistente-de-compras.git
   cd assistente-de-compras
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure a chave da API SerpApi:
   - Crie uma conta em [SerpApi](https://serpapi.com/)
   - Obtenha sua chave de API
   - Defina como variável de ambiente:
     ```bash
     export SERPAPI_KEY="sua_chave_aqui"
     ```
   - Ou edite diretamente no arquivo `serpapi_client.py`

## 🚀 Como Usar

1. Inicie a aplicação:
   ```bash
   python app.py
   ```

2. Acesse no navegador:
   ```
   http://localhost:8080
   ```

3. Digite o nome do produto que deseja buscar e clique em "Buscar"

4. Visualize as 3 melhores ofertas encontradas no Google Shopping

5. Clique em "Exportar para Excel" para baixar os resultados em formato XLSX

## 📊 Exemplo de Uso

1. Busque por "smartphone samsung galaxy"
2. Aguarde enquanto o assistente consulta o Google Shopping
3. Veja as 3 melhores ofertas ordenadas por preço
4. Exporte para Excel ou clique em "Ir para o Carrinho" para acessar diretamente a oferta

## 🔍 Estrutura do Projeto

- `app.py`: Aplicação principal Flask
- `serpapi_client.py`: Cliente para integração com a API SerpApi
- `templates/`: Arquivos HTML da interface
- `static/`: Arquivos CSS, JavaScript e recursos estáticos
- `static/js/`: Scripts para busca e manipulação dos resultados

## 📝 Notas

- Esta aplicação requer uma chave válida da SerpApi para funcionar
- O número de consultas pode ser limitado pelo plano da SerpApi utilizado
- A aplicação é destinada apenas para uso pessoal e educacional

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests com melhorias.

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

---

Desenvolvido como um assistente de compras pessoal para facilitar a comparação de preços online e auxiliar em decisões de compra mais econômicas.
