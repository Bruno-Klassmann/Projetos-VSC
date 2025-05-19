#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de scraping no servidor para o assistente de compras
Este módulo implementa funções de scraping no lado do servidor para sites
que possuem proteções contra scraping no navegador, como o Google Shopping.

Versão com logging detalhado e scraping aprimorado.
"""

import requests
import json
import re
import time
import random
import os
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, parse_qs
import logging
from requests_html import HTMLSession

# --- Configuração de Logging Detalhado ---
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

# Logger principal para o scraper
logger = logging.getLogger("server_scraper")
logger.setLevel(logging.DEBUG)  # Captura todos os níveis de log

# Handler para console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Mostra INFO e acima no console
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# Handler para arquivo (DEBUG)
file_handler_debug = logging.FileHandler(os.path.join(LOG_DIR, "scraper_debug.log"), mode="w")
file_handler_debug.setLevel(logging.DEBUG)
file_handler_debug.setFormatter(log_formatter)
logger.addHandler(file_handler_debug)

# Handler para arquivo (ERROS)
file_handler_error = logging.FileHandler(os.path.join(LOG_DIR, "scraper_error.log"), mode="w")
file_handler_error.setLevel(logging.ERROR)
file_handler_error.setFormatter(log_formatter)
logger.addHandler(file_handler_error)

# Diretório para salvar HTML em caso de erro
HTML_ERROR_DIR = os.path.join(LOG_DIR, "html_errors")
os.makedirs(HTML_ERROR_DIR, exist_ok=True)

# --- Fim da Configuração de Logging ---

class ServerScraper:
    """Classe para realizar scraping no lado do servidor"""

    def __init__(self):
        """Inicializa o scraper com configurações padrão"""
        self.headers = {
            # User-Agent mais comum e recente
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }
        # Usar requests-html para renderizar JavaScript se necessário
        self.session = HTMLSession()
        self.session.headers.update(self.headers)
        self.timeout = 15  # Aumentar timeout
        self.max_retries = 3
        self.retry_delay = 3  # Aumentar delay entre retentativas
        self.render_js = False # Controla se deve renderizar JS (pode ser lento)

    def _save_html_on_error(self, filename, content):
        """Salva o conteúdo HTML em um arquivo para depuração"""
        try:
            filepath = os.path.join(HTML_ERROR_DIR, f"{filename}_{int(time.time())}.html")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"HTML de erro salvo em: {filepath}")
        except Exception as e:
            logger.error(f"Erro ao salvar HTML de erro: {str(e)}")

    def _random_delay(self):
        """Adiciona um atraso aleatório para simular comportamento humano"""
        delay = random.uniform(1.0, 3.0)
        logger.debug(f"Aguardando por {delay:.2f} segundos...")
        time.sleep(delay)

    def search_google_shopping(self, query, max_results=5):
        """
        Realiza uma busca no Google Shopping

        Args:
            query (str): Termo de busca
            max_results (int): Número máximo de resultados a retornar

        Returns:
            list: Lista de produtos encontrados
        """
        results = []
        encoded_query = quote_plus(query)
        # Tentar diferentes URLs/parâmetros do Google Shopping
        urls_to_try = [
            f"https://www.google.com/search?q={encoded_query}&tbm=shop",
            f"https://www.google.com.br/search?q={encoded_query}&tbm=shop&hl=pt-BR&gl=br", # Forçar Brasil
            f"https://www.google.com/search?q={encoded_query}&tbm=shop&source=lnms&sa=X",
        ]

        logger.info(f"Iniciando busca no Google Shopping para: {query}")

        for url in urls_to_try:
            logger.info(f"Tentando URL: {url}")
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"Tentativa {attempt + 1}/{self.max_retries} para URL: {url}")
                    self._random_delay()

                    # Faz a requisição
                    response = self.session.get(url, timeout=self.timeout)
                    logger.debug(f"Status da resposta: {response.status_code}")
                    response.raise_for_status() # Levanta erro para status >= 400

                    # Renderiza JavaScript se habilitado e necessário
                    if self.render_js:
                        logger.debug("Renderizando JavaScript...")
                        response.html.render(sleep=2, timeout=20)
                        html_content = response.html.html
                    else:
                        html_content = response.text

                    # Verifica se a resposta contém um CAPTCHA ou bloqueio
                    if "Our systems have detected unusual traffic" in html_content or "recaptcha" in html_content:
                        logger.warning("Google Shopping detectou tráfego incomum (possível CAPTCHA/bloqueio)")
                        self._save_html_on_error("google_captcha", html_content)
                        # Tentar próxima URL ou tentativa
                        break # Sai do loop de tentativas para esta URL

                    # Analisa o HTML
                    soup = BeautifulSoup(html_content, "html.parser")

                    # Extrai os produtos
                    products = self._extract_google_shopping_products(soup, max_results)

                    if products:
                        logger.info(f"Encontrados {len(products)} produtos na URL: {url}")
                        results.extend(products)
                        # Limita ao número máximo de resultados total
                        results = results[:max_results]
                        return results # Retorna assim que encontrar resultados
                    else:
                        logger.warning(f"Nenhum produto encontrado na tentativa {attempt + 1} para URL: {url}")
                        self._save_html_on_error(f"google_no_products_attempt_{attempt+1}", html_content)

                except requests.exceptions.Timeout:
                    logger.error(f"Timeout na tentativa {attempt + 1} para URL: {url}")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Erro na requisição (tentativa {attempt + 1}) para URL {url}: {str(e)}")
                    if 'response' in locals():
                         self._save_html_on_error(f"google_request_error_attempt_{attempt+1}", response.text)
                except Exception as e:
                    logger.exception(f"Erro inesperado (tentativa {attempt + 1}) para URL {url}: {str(e)}")
                    if 'response' in locals():
                         self._save_html_on_error(f"google_unexpected_error_attempt_{attempt+1}", response.text)

                # Espera antes da próxima tentativa
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    logger.info(f"Aguardando {wait_time}s antes da próxima tentativa...")
                    time.sleep(wait_time)
            # Se esta URL falhou em todas as tentativas, tenta a próxima URL

        logger.warning(f"Não foi possível obter resultados do Google Shopping para {query} após todas as tentativas e URLs.")
        return results # Retorna lista vazia se falhar

    def _extract_google_shopping_products(self, soup, max_results):
        """
        Extrai produtos do HTML do Google Shopping

        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup com o HTML da página
            max_results (int): Número máximo de resultados a retornar

        Returns:
            list: Lista de produtos encontrados
        """
        products = []
        product_elements = []

        # Lista de seletores CSS para encontrar os contêineres dos produtos
        container_selectors = [
            "div.sh-dgr__content",
            "div.sh-dlr__list-result",
            "div.sh-pr__product-results-grid div.sh-pr__product-result",
            "div[data-docid]", # Seletor mais genérico
            ".i0X6df", # Outro seletor observado
            ".u30d4", # Outro seletor observado
        ]

        for selector in container_selectors:
            product_elements = soup.select(selector)
            if product_elements:
                logger.debug(f"Encontrados {len(product_elements)} elementos de produto com o seletor: {selector}")
                break # Usa o primeiro seletor que encontrar resultados
        else:
            logger.warning("Nenhum contêiner de produto encontrado com os seletores conhecidos.")
            return []

        # Lista de seletores para cada campo dentro do contêiner do produto
        name_selectors = ["h3.tAxDx", "h4.A2sOrd", "div.aULzUe", "h3", ".rgHvZc", ".EI11Pd"]
        price_selectors = ["span.a8Pemb", "span.kHxwFf", "span[aria-hidden=\"true\"]", ".PZPZlf span", ".HRLxBb"]
        link_selectors = ["a.shntl", "a.Lq5OHe", "a[href*=\"shopping\"]", "a"]

        extracted_count = 0
        for element in product_elements:
            if extracted_count >= max_results:
                break

            try:
                name = self._extract_field(element, name_selectors, "Nome não encontrado")
                price_text = self._extract_field(element, price_selectors, "Preço não encontrado")
                price = self._format_price(price_text)
                link = self._extract_field(element, link_selectors, None, attribute="href")

                logger.debug(f"Produto Bruto: Nome='{name}', Preço='{price_text}', Link='{link}'")

                if link and link.startswith('/'):
                    link = f"https://www.google.com{link}"

                real_product_link = self._extract_real_product_link(link)

                if price and name != "Nome não encontrado":
                    product_data = {
                        'nome': name,
                        'preco': price,
                        'link': real_product_link or link,
                        'site': 'Google Shopping'
                    }
                    products.append(product_data)
                    logger.debug(f"Produto Extraído: {product_data}")
                    extracted_count += 1
                else:
                    logger.warning(f"Produto ignorado (preço ou nome ausente): Nome='{name}', Preço='{price}'")

            except Exception as e:
                logger.exception(f"Erro ao extrair detalhes de um produto: {str(e)}")

        logger.info(f"Extraídos {len(products)} produtos válidos do Google Shopping.")
        return products

    def _extract_field(self, element, selectors, default_value, attribute=None):
        """Tenta extrair um campo usando uma lista de seletores"""
        for selector in selectors:
            found_element = element.select_one(selector)
            if found_element:
                try:
                    if attribute:
                        value = found_element.get(attribute)
                    else:
                        value = found_element.get_text()

                    if value:
                        return value.strip()
                except Exception as e:
                    logger.debug(f"Erro ao extrair com seletor '{selector}': {str(e)}")
        return default_value

    def _extract_real_product_link(self, google_link):
        """
        Extrai o link real do produto a partir do link do Google Shopping
        (Função aprimorada para lidar com mais casos)
        """
        if not google_link:
            return None

        try:
            # 1. Verifica parâmetros de URL
            parsed_url = urlparse(google_link)
            query_params = parse_qs(parsed_url.query)
            possible_params = ['adurl', 'url', 'q', 'imgrefurl'] # Adicionado imgrefurl
            for param in possible_params:
                if param in query_params:
                    real_url = query_params[param][0]
                    # Validação básica da URL
                    if real_url.startswith('http') and 'google.com' not in urlparse(real_url).netloc:
                        logger.debug(f"Link real encontrado no parâmetro '{param}': {real_url}")
                        return real_url

            # 2. Se for um link direto do Google, tenta seguir redirecionamentos
            if parsed_url.netloc == 'www.google.com' and ('/url?' in parsed_url.path or '/aclk?' in parsed_url.path):
                logger.debug(f"Tentando seguir redirecionamento para: {google_link}")
                try:
                    # Usar HEAD para ser mais rápido e evitar download de conteúdo
                    response = self.session.head(google_link, allow_redirects=True, timeout=5)
                    final_url = response.url
                    if final_url != google_link and 'google.com' not in urlparse(final_url).netloc:
                        logger.debug(f"Link real encontrado após redirecionamento: {final_url}")
                        return final_url
                    else:
                        logger.warning(f"Redirecionamento não levou a um link externo: {final_url}")
                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout ao seguir redirecionamento para: {google_link}")
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Erro ao seguir redirecionamento para {google_link}: {str(e)}")

        except Exception as e:
            logger.exception(f"Erro inesperado ao extrair link real de {google_link}: {str(e)}")

        # Se nada funcionar, retorna o link original do Google
        logger.debug(f"Não foi possível extrair link real, retornando link original: {google_link}")
        return google_link

    def _format_price(self, price_str):
        """
        Formata o preço para um valor numérico (Função aprimorada)
        """
        if not price_str or not isinstance(price_str, str):
            return None

        try:
            logger.debug(f"Formatando preço bruto: {price_str}")
            # Remove símbolos de moeda e espaços extras
            price_str = re.sub(r"(R\$|\$|€|£)\s*", "", price_str).strip()
            # Remove texto adicional (ex: "à vista", "no pix")
            price_str = re.split(r"\s+(a partir de|à vista|no pix)", price_str, flags=re.IGNORECASE)[0]

            # Remove separadores de milhar (ponto ou vírgula)
            # Identifica o separador decimal (última vírgula ou ponto)
            last_comma = price_str.rfind(",")
            last_dot = price_str.rfind(".")

            if last_comma > last_dot: # Decimal é vírgula (formato BR/EU)
                clean_price = price_str.replace(".", "").replace(",", ".")
            elif last_dot > last_comma: # Decimal é ponto (formato US)
                clean_price = price_str.replace(",", "")
            else: # Sem separador decimal ou apenas um tipo
                clean_price = price_str.replace(",", "") # Assume ponto como decimal se existir

            # Remove caracteres não numéricos restantes (exceto o ponto decimal)
            clean_price = re.sub(r"[^\d.]+", "", clean_price)

            if not clean_price:
                return None

            price = float(clean_price)
            logger.debug(f"Preço formatado: {price}")
            return price
        except Exception as e:
            logger.exception(f"Erro ao formatar preço {price_str}: {str(e)}")
            return None

# Função para teste direto
if __name__ == "__main__":
    logger.info("--- Iniciando teste do ServerScraper ---")
    scraper = ServerScraper()
    # Teste com um produto específico
    query = "notebook dell xps 13"
    logger.info(f"Buscando por: {query}")
    results = scraper.search_google_shopping(query)
    print("--- Resultados da Busca ---")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info("--- Teste concluído ---")
