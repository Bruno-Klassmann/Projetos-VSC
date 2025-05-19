#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('storage')

class ResultStorage:
    """
    Classe para gerenciar o armazenamento de resultados de busca
    """
    def __init__(self, results_dir):
        """
        Inicializa o armazenamento de resultados
        
        Args:
            results_dir (str): Diretório para armazenar os resultados
        """
        self.results_dir = results_dir
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            logger.info(f"Diretório de resultados criado: {self.results_dir}")
    
    def save_results(self, data):
        """
        Salva os resultados de uma busca
        
        Args:
            data (dict): Dados da busca a serem salvos
            
        Returns:
            dict: Informações sobre o arquivo salvo
        """
        if not data or 'query' not in data:
            raise ValueError("Dados inválidos para salvar")
        
        # Cria um nome de arquivo baseado na consulta e timestamp
        query_slug = data["query"].lower().replace(" ", "_")[:30]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{query_slug}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        # Adiciona metadados ao resultado
        data['metadata'] = {
            'saved_at': datetime.now().isoformat(),
            'source': 'browser_scraping',
            'version': '1.0'
        }
        
        # Salva os resultados em JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Resultados salvos em {filepath}")
        
        return {
            'success': True,
            'file': filename,
            'path': filepath,
            'timestamp': timestamp
        }
    
    def get_recent_searches(self, limit=10):
        """
        Retorna as buscas recentes
        
        Args:
            limit (int): Número máximo de buscas a retornar
            
        Returns:
            list: Lista de buscas recentes
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
                        
                        # Extrai informações básicas
                        search_info = {
                            'query': data.get('query', 'Busca desconhecida'),
                            'timestamp': data.get('timestamp', 'Data desconhecida'),
                            'file': file,
                            'sites': list(data.get('results', {}).keys()),
                            'has_best_deal': 'best_overall' in data and data['best_overall'] is not None,
                            'metadata': data.get('metadata', {})
                        }
                        
                        recent_searches.append(search_info)
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
        
        Args:
            filename (str): Nome do arquivo de resultados
            
        Returns:
            dict: Dados da busca
        """
        filepath = os.path.join(self.results_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Arquivo não encontrado: {filename}")
            
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return data
    
    def delete_search_result(self, filename):
        """
        Exclui um arquivo de resultados
        
        Args:
            filename (str): Nome do arquivo a ser excluído
            
        Returns:
            bool: True se o arquivo foi excluído com sucesso
        """
        filepath = os.path.join(self.results_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Arquivo não encontrado: {filename}")
        
        os.remove(filepath)
        logger.info(f"Arquivo excluído: {filepath}")
        
        return True
    
    def clear_old_results(self, days=30):
        """
        Remove resultados antigos
        
        Args:
            days (int): Número de dias para considerar um resultado como antigo
            
        Returns:
            int: Número de arquivos removidos
        """
        now = time.time()
        count = 0
        
        for filename in os.listdir(self.results_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.results_dir, filename)
                file_time = os.path.getmtime(filepath)
                
                # Se o arquivo for mais antigo que o número de dias especificado
                if (now - file_time) / (24 * 3600) > days:
                    try:
                        os.remove(filepath)
                        count += 1
                        logger.info(f"Arquivo antigo removido: {filepath}")
                    except Exception as e:
                        logger.error(f"Erro ao remover arquivo {filepath}: {e}")
        
        return count
    
    def get_storage_stats(self):
        """
        Retorna estatísticas sobre o armazenamento
        
        Returns:
            dict: Estatísticas do armazenamento
        """
        try:
            files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
            
            # Calcula o tamanho total
            total_size = sum(os.path.getsize(os.path.join(self.results_dir, f)) for f in files)
            
            # Obtém a data do arquivo mais recente e mais antigo
            if files:
                files_with_time = [(f, os.path.getmtime(os.path.join(self.results_dir, f))) for f in files]
                newest_file = max(files_with_time, key=lambda x: x[1])
                oldest_file = min(files_with_time, key=lambda x: x[1])
                
                newest_time = datetime.fromtimestamp(newest_file[1]).isoformat()
                oldest_time = datetime.fromtimestamp(oldest_file[1]).isoformat()
            else:
                newest_time = None
                oldest_time = None
            
            return {
                'total_files': len(files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'newest_file_time': newest_time,
                'oldest_file_time': oldest_time,
                'storage_dir': self.results_dir
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de armazenamento: {e}")
            return {
                'error': str(e),
                'storage_dir': self.results_dir
            }
