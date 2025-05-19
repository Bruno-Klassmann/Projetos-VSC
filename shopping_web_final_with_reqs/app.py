#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de integração com a API do assistente de compras
Este módulo implementa endpoints para busca de produtos no Google Shopping via SerpApi
e exportação dos resultados para XLSX.
"""

from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from flask_cors import CORS
import os
import json
import time
import datetime
import requests
import logging
from urllib.parse import unquote
from serpapi_client import SerpApiClient
import pandas as pd
import io

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger('shopping_api')

# Inicializa a aplicação Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Diretório para armazenar resultados e arquivos temporários
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Inicializa o cliente SerpApi
serpapi_client = SerpApiClient()

@app.route('/')
def index():
    """Renderiza a página inicial"""
    return render_template('index.html')

@app.route('/api/search/top-deals')
def search_top_deals():
    """
    Endpoint para buscar as 3 melhores ofertas no Google Shopping
    """
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query não fornecida'}), 400
    
    try:
        # Busca no Google Shopping via SerpApi
        logger.info(f"Buscando melhores ofertas para: {query}")
        results = serpapi_client.search_google_shopping(query, max_results=10)
        
        # Ordena por preço (do menor para o maior)
        sorted_results = sorted(results, key=lambda x: x.get('preco', float('inf')))
        
        # Retorna apenas os 3 melhores resultados
        top_results = sorted_results[:3] if len(sorted_results) >= 3 else sorted_results
        
        # Adiciona links de carrinho (se disponíveis) - A SerpApi pode não fornecer isso diretamente
        # Aqui, estamos usando o link do produto como fallback
        for result in top_results:
            result['cart_link_final'] = result.get('cart_link') or result.get('link')
            
        return jsonify({
            'query': query,
            'timestamp': datetime.datetime.now().isoformat(),
            'top_deals': top_results
        })
    
    except Exception as e:
        logger.error(f"Erro na busca de melhores ofertas: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-xlsx', methods=['POST'])
def export_xlsx():
    """
    Gera e retorna um arquivo XLSX com os resultados da busca.
    """
    try:
        data = request.json
        if not data or 'top_deals' not in data:
            return jsonify({'error': 'Dados inválidos ou ausentes'}), 400

        query = data.get('query', 'busca')
        top_deals = data.get('top_deals', [])

        if not top_deals:
            return jsonify({'error': 'Nenhuma oferta para exportar'}), 400

        # Prepara os dados para o DataFrame
        export_data = []
        for i, deal in enumerate(top_deals):
            export_data.append({
                'Ranking': i + 1,
                'Produto': deal.get('nome', 'N/A'),
                'Preço': deal.get('preco', None),
                'Link Oferta': deal.get('link', 'Link não disponível'),
                'Link Carrinho': deal.get('cart_link_final', 'Link não disponível') # Usa o link final
            })

        # Cria o DataFrame
        df = pd.DataFrame(export_data)

        # Cria o arquivo XLSX em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Melhores Ofertas')
            # Ajusta a largura das colunas (opcional)
            worksheet = writer.sheets['Melhores Ofertas']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter # Get the column name
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                worksheet.column_dimensions[column_letter].width = adjusted_width
            # Formata a coluna de preço como moeda
            price_col_letter = 'C' # Assumindo que Preço é a coluna C
            for cell in worksheet[price_col_letter][1:]: # Pula o cabeçalho
                cell.number_format = 'R$ #,##0.00'

        output.seek(0)

        # Define o nome do arquivo
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"melhores_ofertas_{query.replace(' ', '_')}_{timestamp}.xlsx"

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Erro ao exportar XLSX: {str(e)}")
        return jsonify({'error': f'Erro ao gerar arquivo XLSX: {str(e)}'}), 500

@app.route('/api/save-results', methods=['POST'])
def save_results():
    """
    Salva os resultados de uma busca
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Gera um nome de arquivo baseado na query e timestamp
        query = data.get('query', 'unknown')
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{query.replace(' ', '_')}_{timestamp}.json"
        
        # Salva os resultados em um arquivo JSON
        filepath = os.path.join(RESULTS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'file': filename
        })
    
    except Exception as e:
        logger.error(f"Erro ao salvar resultados: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent')
def get_recent_searches():
    """
    Retorna as buscas recentes
    """
    try:
        # Lista os arquivos no diretório de resultados
        files = os.listdir(RESULTS_DIR)
        files = [f for f in files if f.endswith('json')]
        
        # Ordena por data de modificação (mais recente primeiro)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(RESULTS_DIR, x)), reverse=True)
        
        # Limita a 10 resultados
        files = files[:10]
        
        # Carrega os dados de cada arquivo
        recent_searches = []
        for filename in files:
            filepath = os.path.join(RESULTS_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    recent_searches.append({
                        'query': data.get('query', 'Busca desconhecida'),
                        'timestamp': data.get('timestamp', 'Data desconhecida'),
                        'file': filename
                    })
            except Exception as e:
                logger.error(f"Erro ao ler arquivo {filename}: {str(e)}")
        
        return jsonify(recent_searches)
    
    except Exception as e:
        logger.error(f"Erro ao obter buscas recentes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/results/<filename>')
def get_results(filename):
    """
    Retorna os resultados de uma busca específica
    """
    try:
        filepath = os.path.join(RESULTS_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Arquivo não encontrado'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data)
    
    except Exception as e:
        logger.error(f"Erro ao obter resultados: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """
    Retorna o status da API
    """
    try:
        # Verifica se a SerpApi está funcionando
        serpapi_status = "ok"
        try:
            # Faz uma busca simples para testar
            serpapi_client.search_google_shopping("test", max_results=1)
        except Exception as e:
            serpapi_status = f"error: {str(e)}"
        
        return jsonify({
            'status': 'online',
            'serpapi_status': serpapi_status,
            'timestamp': datetime.datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Erro ao obter status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve arquivos estáticos"""
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
