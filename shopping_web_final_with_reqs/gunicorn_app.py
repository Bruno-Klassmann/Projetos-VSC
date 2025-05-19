#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from gunicorn.app.base import BaseApplication
from app import app

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gunicorn_config')

class StandaloneApplication(BaseApplication):
    """Aplicação Gunicorn standalone para produção"""
    
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()
        
    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)
                
    def load(self):
        return self.application

if __name__ == "__main__":
    # Configurações do Gunicorn
    options = {
        'bind': '0.0.0.0:8080',
        'workers': 3,
        'worker_class': 'sync',
        'timeout': 120,  # Timeout maior para permitir scraping
        'accesslog': '-',
        'errorlog': '-',
        'loglevel': 'info',
        'preload_app': True
    }
    
    logger.info("Iniciando servidor Gunicorn para produção")
    StandaloneApplication(app, options).run()
