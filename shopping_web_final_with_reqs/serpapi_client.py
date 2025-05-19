#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de integração com a SerpApi para o assistente de compras
Este módulo implementa funções para buscar produtos no Google Shopping
usando a SerpApi como alternativa ao scraping direto.
"""

import requests
import json
import time
import os
import logging
from urllib.parse import quote_plus

# --- Configuração de Logging ---
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

# Logger principal
logger = logging.getLogger("serpapi_client")
logger.setLevel(logging.DEBUG)

# Handler para console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# Handler para arquivo (DEBUG)
file_handler_debug = logging.FileHandler(os.path.join(LOG_DIR, "serpapi_debug.log"), mode="w")
file_handler_debug.setLevel(logging.DEBUG)
file_handler_debug.setFormatter(log_formatter)
logger.addHandler(file_handler_debug)

# Handler para arquivo (ERROS)
file_handler_error = logging.FileHandler(os.path.join(LOG_DIR, "serpapi_error.log"), mode="w")
file_handler_error.setLevel(logging.ERROR)
file_handler_error.setFormatter(log_formatter)
logger.addHandler(file_handler_error)

class SerpApiClient:
    """Cliente para a SerpApi para buscar produtos no Google Shopping"""
    
    def __init__(self, api_key=None):
        """
        Inicializa o cliente da SerpApi
        
        Args:
            api_key (str, optional): Chave de API da SerpApi. Se não fornecida,
                                    tentará ler da variável de ambiente SERPAPI_KEY.
        """
        self.api_key = api_key or os.environ.get("SERPAPI_KEY") or "3a744873e4a44b8b87e92229d8172c29e58b7547966aa543eecc43e55ea456f4"
        self.base_url = "https://serpapi.com/search"
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 2
        
        logger.info("Cliente SerpApi inicializado")
        
    def search_google_shopping(self, query, max_results=5, country="br", language="pt"):
        """
        Busca produtos no Google Shopping usando a SerpApi
        
        Args:
            query (str): Termo de busca
            max_results (int): Número máximo de resultados a retornar
            country (str): Código do país (ex: "br" para Brasil)
            language (str): Código do idioma (ex: "pt" para Português)
            
        Returns:
            list: Lista de produtos encontrados
        """
        logger.info(f"Buscando no Google Shopping via SerpApi: {query}")
        
        # Parâmetros da requisição
        params = {
            "api_key": self.api_key,
            "engine": "google_shopping",
            "q": query,
            "google_domain": f"google.com.{country}",
            "gl": country,
            "hl": language,
            "num": max_results
        }
        
        # Tenta fazer a requisição com retentativas
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Tentativa {attempt + 1}/{self.max_retries} para buscar: {query}")
                
                # Adiciona um atraso entre tentativas
                if attempt > 0:
                    time.sleep(self.retry_delay * attempt)
                
                # Faz a requisição
                response = requests.get(
                    self.base_url,
                    params=params,
                    timeout=self.timeout
                )
                
                # Verifica se a resposta foi bem-sucedida
                response.raise_for_status()
                
                # Converte a resposta para JSON
                data = response.json()
                
                # Verifica se há resultados de shopping
                if "shopping_results" not in data:
                    logger.warning(f"Nenhum resultado de shopping encontrado para: {query}")
                    continue
                
                # Processa os resultados
                results = self._process_shopping_results(data["shopping_results"], max_results)
                
                logger.info(f"Encontrados {len(results)} produtos para: {query}")
                return results
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Erro na requisição à SerpApi (tentativa {attempt + 1}): {str(e)}")
                
                if attempt == self.max_retries - 1:
                    logger.error("Todas as tentativas falharam")
                    return []
        
        return []
    
    def _process_shopping_results(self, shopping_results, max_results):
        """
        Processa os resultados da SerpApi para o formato usado pelo assistente
        
        Args:
            shopping_results (list): Lista de resultados da SerpApi
            max_results (int): Número máximo de resultados a retornar
            
        Returns:
            list: Lista de produtos processados
        """
        products = []
        
        for item in shopping_results[:max_results]:
            logger.debug(f"Raw item: {item}")
            try:
                # Extrai os dados do produto
                name = item.get("title", "Nome não encontrado")
                
                # Extrai o preço como número
                price = None
                if "extracted_price" in item and item["extracted_price"]:
                    price = float(item["extracted_price"])
                
                # Obtém o link do produto
                link = item.get("product_link", "")
                
                # Obtém o link para o carrinho (mesmo link do produto no caso do Google Shopping)
                cart_link = item.get("product_link", "")
                
                # Adiciona o produto à lista se tiver preço
                if price:
                    product = {
                        "nome": name,
                        "preco": price,
                        "link": link,
                        "cart_link": cart_link,
                        "site": "Google Shopping"
                    }
                    products.append(product)
                    logger.debug(f"Produto processado: {product}")
                else:
                    logger.warning(f"Produto ignorado (sem preço): {name}")
                    
            except Exception as e:
                logger.exception(f"Erro ao processar produto: {str(e)}")
        
        return products

# Função para teste direto
if __name__ == "__main__":
    logger.info("--- Iniciando teste do SerpApiClient ---")
    client = SerpApiClient()
    # Teste com um produto específico
    query = "notebook dell xps 13"
    logger.info(f"Buscando por: {query}")
    results = client.search_google_shopping(query)
    print("--- Resultados da Busca ---")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info("--- Teste concluído ---")
