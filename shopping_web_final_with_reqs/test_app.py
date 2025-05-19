#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import requests
import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import subprocess
import signal
import json

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test')

class ShoppingWebAppTest(unittest.TestCase):
    """Testes para a aplicação web do Assistente de Compras"""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes"""
        # Inicia o servidor Flask em um processo separado
        cls.flask_process = subprocess.Popen(
            ["python3", "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        # Aguarda o servidor iniciar
        time.sleep(3)
        
        # Configura o driver do Selenium
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # URL base para testes
        cls.base_url = "http://localhost:5000"
        
        logger.info("Configuração de testes concluída")
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes"""
        # Fecha o driver do Selenium
        if cls.driver:
            cls.driver.quit()
        
        # Encerra o servidor Flask
        if cls.flask_process:
            os.killpg(os.getpgid(cls.flask_process.pid), signal.SIGTERM)
            stdout, stderr = cls.flask_process.communicate()
            if stdout:
                logger.info(f"Flask stdout: {stdout.decode('utf-8')}")
            if stderr:
                logger.error(f"Flask stderr: {stderr.decode('utf-8')}")
        
        logger.info("Limpeza de testes concluída")
    
    def test_01_home_page_loads(self):
        """Testa se a página inicial carrega corretamente"""
        logger.info("Testando carregamento da página inicial")
        
        self.driver.get(self.base_url)
        
        # Verifica se o título está correto
        self.assertIn("Assistente de Compras", self.driver.title)
        
        # Verifica se os elementos principais estão presentes
        search_input = self.driver.find_element(By.ID, "search-input")
        search_button = self.driver.find_element(By.ID, "search-button")
        
        self.assertIsNotNone(search_input)
        self.assertIsNotNone(search_button)
        
        logger.info("Teste de carregamento da página inicial concluído com sucesso")
    
    def test_02_api_endpoints(self):
        """Testa se os endpoints da API estão funcionando"""
        logger.info("Testando endpoints da API")
        
        # Testa o endpoint de buscas recentes
        response = requests.get(f"{self.base_url}/api/recent")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        
        # Testa o endpoint de busca com uma query inválida
        response = requests.post(
            f"{self.base_url}/api/search",
            json={"query": ""}
        )
        self.assertEqual(response.status_code, 400)
        
        logger.info("Teste de endpoints da API concluído com sucesso")
    
    def test_03_search_functionality(self):
        """Testa a funcionalidade de busca via API"""
        logger.info("Testando funcionalidade de busca via API")
        
        # Este teste pode demorar mais tempo, pois faz uma busca real
        # Definimos um timeout maior para a resposta
        test_query = "smartphone samsung"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/search",
                json={"query": test_query},
                timeout=60  # 60 segundos de timeout
            )
            
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertEqual(data["query"], test_query)
            self.assertIn("results", data)
            self.assertIn("timestamp", data)
            
            # Verifica se há resultados para pelo menos um site
            sites_with_results = 0
            for site, info in data["results"].items():
                if info["nome"] != "Nenhum produto encontrado":
                    sites_with_results += 1
            
            logger.info(f"Sites com resultados: {sites_with_results}")
            # Pelo menos um site deve ter resultados
            self.assertGreater(sites_with_results, 0)
            
            logger.info("Teste de funcionalidade de busca via API concluído com sucesso")
        except requests.exceptions.Timeout:
            logger.error("Timeout durante a busca")
            self.fail("Timeout durante a busca")
        except Exception as e:
            logger.error(f"Erro durante o teste de busca: {e}")
            self.fail(f"Erro durante o teste de busca: {e}")
    
    def test_04_ui_search_interaction(self):
        """Testa a interação de busca na interface do usuário"""
        logger.info("Testando interação de busca na UI")
        
        self.driver.get(self.base_url)
        
        # Preenche o campo de busca
        search_input = self.driver.find_element(By.ID, "search-input")
        search_input.clear()
        search_input.send_keys("notebook dell")
        
        # Clica no botão de busca
        search_button = self.driver.find_element(By.ID, "search-button")
        search_button.click()
        
        try:
            # Aguarda os resultados aparecerem (pode demorar devido ao scraping)
            WebDriverWait(self.driver, 90).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "results-container"))
            )
            
            # Verifica se a seção de resultados está visível
            results_section = self.driver.find_element(By.ID, "results-section")
            self.assertTrue(results_section.is_displayed())
            
            # Verifica se há cards de sites
            site_cards = self.driver.find_elements(By.CLASS_NAME, "site-card")
            self.assertGreater(len(site_cards), 0)
            
            logger.info("Teste de interação de busca na UI concluído com sucesso")
        except Exception as e:
            logger.error(f"Erro durante o teste de UI: {e}")
            self.fail(f"Erro durante o teste de UI: {e}")
    
    def test_05_recent_searches(self):
        """Testa a funcionalidade de buscas recentes"""
        logger.info("Testando funcionalidade de buscas recentes")
        
        # Após os testes anteriores, deve haver pelo menos uma busca recente
        self.driver.get(self.base_url)
        
        try:
            # Aguarda a lista de buscas recentes carregar
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "recent-list"))
            )
            
            # Verifica se há itens na lista de buscas recentes
            recent_items = self.driver.find_elements(By.CLASS_NAME, "recent-item")
            
            # Deve haver pelo menos uma busca recente (das buscas dos testes anteriores)
            self.assertGreater(len(recent_items), 0)
            
            logger.info("Teste de buscas recentes concluído com sucesso")
        except Exception as e:
            logger.error(f"Erro durante o teste de buscas recentes: {e}")
            self.fail(f"Erro durante o teste de buscas recentes: {e}")

def run_tests():
    """Executa os testes da aplicação web"""
    logger.info("Iniciando testes da aplicação web")
    
    # Cria o diretório de resultados de testes se não existir
    test_results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results")
    if not os.path.exists(test_results_dir):
        os.makedirs(test_results_dir)
    
    # Executa os testes
    test_suite = unittest.TestLoader().loadTestsFromTestCase(ShoppingWebAppTest)
    test_result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Salva os resultados em um arquivo JSON
    results = {
        "total": test_result.testsRun,
        "success": test_result.wasSuccessful(),
        "failures": len(test_result.failures),
        "errors": len(test_result.errors),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "details": {
            "failures": [{"test": f[0].id(), "message": f[1]} for f in test_result.failures],
            "errors": [{"test": e[0].id(), "message": e[1]} for e in test_result.errors]
        }
    }
    
    results_file = os.path.join(test_results_dir, f"test_results_{time.strftime('%Y%m%d_%H%M%S')}.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    logger.info(f"Resultados dos testes salvos em {results_file}")
    
    # Exibe um resumo dos resultados
    print("\n=== RESUMO DOS TESTES ===")
    print(f"Total de testes: {results['total']}")
    print(f"Testes bem-sucedidos: {results['total'] - results['failures'] - results['errors']}")
    print(f"Falhas: {results['failures']}")
    print(f"Erros: {results['errors']}")
    print(f"Sucesso geral: {'Sim' if results['success'] else 'Não'}")
    
    return results

if __name__ == "__main__":
    run_tests()
