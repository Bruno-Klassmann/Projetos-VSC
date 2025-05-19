#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import logging
import threading
from datetime import datetime
from scraper import ProductScraper

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('shopping_api')

class ShoppingAPI:
    def __init__(self, results_dir):
        self.results_dir = results_dir
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        # Cache para evitar buscas repetidas em curto período
        self.search_cache = {}
        # Lock para evitar múltiplas buscas simultâneas
        self.search_lock = threading.Lock()
        
    def search_products(self, query):
        """
        Busca produtos com base na query fornecida
        Retorna os resultados formatados e o caminho do arquivo JSON
        """
        if not query or not query.strip():
            raise ValueError("Query não pode ser vazia")
            
        query = query.strip()
        
        # Verifica se já existe no cache (menos de 5 minutos)
        cache_key = query.lower()
        current_time = time.time()
        
        if cache_key in self.search_cache:
            cache_time, cache_results = self.search_cache[cache_key]
            # Se o cache tem menos de 5 minutos, retorna os resultados em cache
            if current_time - cache_time < 300:  # 5 minutos em segundos
                logger.info(f"Retornando resultados em cache para: {query}")
                return cache_results, None
        
        # Usa lock para evitar múltiplas buscas simultâneas do mesmo termo
        if not self.search_lock.acquire(blocking=False):
            raise RuntimeError("Busca em andamento, tente novamente em alguns instantes")
        
        try:
            # Inicializa o scraper
            scraper = ProductScraper()
            
            # Busca os produtos
            logger.info(f"Iniciando busca para: {query}")
            results = scraper.search_all_sites(query)
            
            # Encontra as melhores ofertas
            best_deals = self._find_best_deals(results, scraper)
            
            # Formata os resultados
            formatted_results = self._format_results(best_deals, query)
            
            # Salva os resultados em JSON
            json_filepath = self._save_results(formatted_results)
            
            # Atualiza o cache
            self.search_cache[cache_key] = (current_time, formatted_results)
            
            return formatted_results, json_filepath
            
        except Exception as e:
            logger.error(f"Erro durante a busca: {e}")
            raise
        finally:
            self.search_lock.release()
            
    def _find_best_deals(self, results, scraper):
        """
        Encontra as melhores ofertas por site e a melhor oferta geral
        """
        best_deals = {
            "Google Shopping": None,
            "Mercado Livre": None,
            "Kabum": None,
            "Melhor Oferta": None
        }
        
        # Agrupa por site
        for site in ["Google Shopping", "Mercado Livre", "Kabum"]:
            site_results = [r for r in results if r["site"] == site]
            
            # Encontra o produto com menor preço para cada site
            if site_results:
                best_deal = min(site_results, key=lambda x: x["preco"])
                
                # Tenta obter o link do carrinho
                cart_link = scraper.get_cart_link(best_deal["link"], site)
                best_deal["cart_link"] = cart_link
                
                best_deals[site] = best_deal
        
        # Encontra a melhor oferta geral (menor preço entre todos os sites)
        valid_deals = [deal for deal in [best_deals["Google Shopping"], 
                                        best_deals["Mercado Livre"], 
                                        best_deals["Kabum"]] 
                      if deal is not None]
        
        if valid_deals:
            best_overall = min(valid_deals, key=lambda x: x["preco"])
            best_deals["Melhor Oferta"] = best_overall
        
        return best_deals
        
    def _calculate_savings(self, best_price, results):
        """
        Calcula a economia em relação ao segundo melhor preço
        """
        # Coleta todos os preços válidos (exceto o melhor)
        prices = [site_info["preco_valor"] for site, site_info in results.items() 
                 if site_info["preco_valor"] != float('inf') and site_info["preco_valor"] > best_price]
        
        if not prices:
            return "Único preço disponível"
        
        # Encontra o segundo melhor preço
        second_best = min(prices)
        
        # Calcula a economia
        savings = second_best - best_price
        savings_percent = (savings / second_best) * 100
        
        return f"Economia de R$ {savings:.2f} ({savings_percent:.1f}%)".replace('.', ',')
        
    def _format_results(self, best_deals, query):
        """
        Formata os resultados para exibição
        """
        output = {
            "query": query,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": {},
            "best_overall": None
        }
        
        for site in ["Google Shopping", "Mercado Livre", "Kabum"]:
            deal = best_deals[site]
            if deal:
                output["results"][site] = {
                    "nome": deal["nome"],
                    "preco": f"R$ {deal['preco']:.2f}".replace('.', ','),
                    "preco_valor": deal['preco'],  # Mantém o valor numérico para comparações
                    "link": deal["link"],
                    "cart_link": deal.get("cart_link", deal["link"])
                }
            else:
                output["results"][site] = {
                    "nome": "Nenhum produto encontrado",
                    "preco": "N/A",
                    "preco_valor": float('inf'),  # Valor infinito para comparações
                    "link": None,
                    "cart_link": None
                }
        
        # Adiciona informação sobre a melhor oferta geral
        if best_deals["Melhor Oferta"]:
            best = best_deals["Melhor Oferta"]
            output["best_overall"] = {
                "site": best["site"],
                "nome": best["nome"],
                "preco": f"R$ {best['preco']:.2f}".replace('.', ','),
                "preco_valor": best['preco'],
                "economia": self._calculate_savings(best["preco"], output["results"]),
                "link": best["link"],
                "cart_link": best.get("cart_link", best["link"])
            }
                
        return output
    
    def _save_results(self, formatted_results):
        """
        Salva os resultados em um arquivo JSON
        """
        # Cria um nome de arquivo baseado na consulta e timestamp
        query_slug = formatted_results["query"].lower().replace(" ", "_")[:30]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{query_slug}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(formatted_results, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Resultados salvos em {filepath}")
        return filepath
        
    def get_recent_searches(self, limit=10):
        """
        Retorna as buscas recentes
        """
        try:
            # Lista os arquivos no diretório de resultados
            files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
            files.sort(key=lambda x: os.path.getmtime(os.path.join(self.results_dir, x)), reverse=True)
            
            # Limita ao número especificado
            recent_files = files[:limit]
            
            recent_searches = []
            for file in recent_files:
                try:
                    with open(os.path.join(self.results_dir, file), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        recent_searches.append({
                            'query': data['query'],
                            'timestamp': data['timestamp'],
                            'file': file
                        })
                except Exception as e:
                    logger.error(f"Erro ao ler arquivo {file}: {e}")
                    continue
            
            return recent_searches
        except Exception as e:
            logger.error(f"Erro ao listar buscas recentes: {e}")
            return []
            
    def get_search_results(self, filename):
        """
        Retorna os resultados de uma busca específica
        """
        try:
            filepath = os.path.join(self.results_dir, filename)
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Arquivo não encontrado: {filename}")
                
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return data
        except Exception as e:
            logger.error(f"Erro ao ler resultados: {e}")
            raise
