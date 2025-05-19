#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import json
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scraper')

class ProductScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.driver = None
        
    def setup_selenium(self):
        """Configura o driver do Selenium para navegação headless"""
        if self.driver:
            return
            
        logger.info("Configurando driver do Selenium")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")
        
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            logger.info("Driver do Selenium configurado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao configurar driver do Selenium: {e}")
            raise
        
    def close_driver(self):
        """Fecha o driver do Selenium"""
        if hasattr(self, 'driver') and self.driver:
            logger.info("Fechando driver do Selenium")
            self.driver.quit()
            self.driver = None
            
    def format_price(self, price_str):
        """Formata o preço para um valor numérico"""
        if not price_str:
            return None
            
        # Remove caracteres não numéricos, mantendo o ponto decimal
        price_str = re.sub(r'[^\d,]', '', price_str)
        # Substitui vírgula por ponto para formato numérico
        price_str = price_str.replace(',', '.')
        
        try:
            return float(price_str)
        except ValueError:
            return None
            
    def search_google_shopping(self, query):
        """Busca produtos no Google Shopping"""
        logger.info(f"Buscando no Google Shopping: {query}")
        results = []
        
        # Formata a query para URL
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded_query}&tbm=shop"
        
        try:
            self.setup_selenium()
            self.driver.get(url)
            # Aguarda o carregamento dos resultados
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.sh-dgr__content"))
            )
            
            # Extrai os resultados
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.sh-dgr__content")
            
            for element in product_elements[:5]:  # Limita a 5 resultados
                try:
                    name_element = element.find_element(By.CSS_SELECTOR, "h3.tAxDx")
                    name = name_element.text if name_element else "Nome não encontrado"
                    
                    price_element = element.find_element(By.CSS_SELECTOR, "span.a8Pemb")
                    price_text = price_element.text if price_element else "Preço não encontrado"
                    price = self.format_price(price_text)
                    
                    # Tenta obter o link do produto
                    link_element = element.find_element(By.CSS_SELECTOR, "a.shntl")
                    link = link_element.get_attribute("href") if link_element else None
                    
                    # Adiciona o resultado se tiver preço
                    if price:
                        results.append({
                            "nome": name,
                            "preco": price,
                            "link": link,
                            "site": "Google Shopping"
                        })
                except Exception as e:
                    logger.warning(f"Erro ao extrair produto do Google Shopping: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Erro ao buscar no Google Shopping: {e}")
            
        return results
        
    def search_mercado_livre(self, query):
        """Busca produtos no Mercado Livre"""
        logger.info(f"Buscando no Mercado Livre: {query}")
        results = []
        
        # Formata a query para URL
        encoded_query = urllib.parse.quote(query)
        url = f"https://lista.mercadolivre.com.br/{encoded_query}"
        
        try:
            self.setup_selenium()
            self.driver.get(url)
            # Aguarda o carregamento dos resultados
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.ui-search-layout__item"))
            )
            
            # Extrai os resultados
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, "li.ui-search-layout__item")
            
            for element in product_elements[:5]:  # Limita a 5 resultados
                try:
                    name_element = element.find_element(By.CSS_SELECTOR, "h2.ui-search-item__title")
                    name = name_element.text if name_element else "Nome não encontrado"
                    
                    price_element = element.find_element(By.CSS_SELECTOR, "span.andes-money-amount__fraction")
                    price_text = price_element.text if price_element else "0"
                    
                    # Verifica se há centavos
                    cents_element = element.find_elements(By.CSS_SELECTOR, "span.andes-money-amount__cents")
                    if cents_element and len(cents_element) > 0:
                        cents = cents_element[0].text
                        price_text = f"{price_text},{cents}"
                    
                    price = self.format_price(price_text)
                    
                    # Tenta obter o link do produto
                    link_element = element.find_element(By.CSS_SELECTOR, "a.ui-search-link")
                    link = link_element.get_attribute("href") if link_element else None
                    
                    # Adiciona o resultado se tiver preço
                    if price:
                        results.append({
                            "nome": name,
                            "preco": price,
                            "link": link,
                            "site": "Mercado Livre"
                        })
                except Exception as e:
                    logger.warning(f"Erro ao extrair produto do Mercado Livre: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Erro ao buscar no Mercado Livre: {e}")
            
        return results
        
    def search_kabum(self, query):
        """Busca produtos na Kabum"""
        logger.info(f"Buscando na Kabum: {query}")
        results = []
        
        # Formata a query para URL
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.kabum.com.br/busca/{encoded_query}"
        
        try:
            self.setup_selenium()
            self.driver.get(url)
            # Aguarda o carregamento dos resultados
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.productCard"))
            )
            
            # Extrai os resultados
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.productCard")
            
            for element in product_elements[:5]:  # Limita a 5 resultados
                try:
                    name_element = element.find_element(By.CSS_SELECTOR, "span.nameCard")
                    name = name_element.text if name_element else "Nome não encontrado"
                    
                    price_element = element.find_element(By.CSS_SELECTOR, "span.priceCard")
                    price_text = price_element.text if price_element else "Preço não encontrado"
                    price = self.format_price(price_text)
                    
                    # Tenta obter o link do produto
                    link_element = element.find_element(By.CSS_SELECTOR, "a.productLink")
                    link = link_element.get_attribute("href") if link_element else None
                    
                    # Adiciona o resultado se tiver preço
                    if price:
                        results.append({
                            "nome": name,
                            "preco": price,
                            "link": link,
                            "site": "Kabum"
                        })
                except Exception as e:
                    logger.warning(f"Erro ao extrair produto da Kabum: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Erro ao buscar na Kabum: {e}")
            
        return results
        
    def get_cart_link(self, product_url, site):
        """Tenta obter o link direto para adicionar ao carrinho"""
        if not product_url:
            return None
            
        if site == "Mercado Livre":
            # No Mercado Livre, o link do produto já é suficiente
            # O usuário pode adicionar ao carrinho na página do produto
            return product_url
        elif site == "Kabum":
            # Na Kabum, podemos tentar adicionar diretamente ao carrinho
            # Formato pode variar, então retornamos o link do produto
            return product_url
        elif site == "Google Shopping":
            # No Google Shopping, o link já redireciona para a loja
            return product_url
            
        return product_url
        
    def search_all_sites(self, query):
        """Busca produtos em todos os sites e retorna os resultados combinados"""
        logger.info(f"Iniciando busca em todos os sites para: {query}")
        
        try:
            # Busca em cada site
            google_results = self.search_google_shopping(query)
            ml_results = self.search_mercado_livre(query)
            kabum_results = self.search_kabum(query)
            
            # Combina os resultados
            all_results = google_results + ml_results + kabum_results
            
            logger.info(f"Busca concluída. Total de resultados: {len(all_results)}")
            return all_results
            
        except Exception as e:
            logger.error(f"Erro durante a busca em todos os sites: {e}")
            return []
        finally:
            # Sempre fecha o driver ao finalizar
            self.close_driver()
