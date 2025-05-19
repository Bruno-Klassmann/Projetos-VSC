#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import subprocess
import signal
import time

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('deploy')

def check_server_status():
    """Verifica se o servidor está em execução"""
    try:
        # Verifica se há processos gunicorn em execução
        result = subprocess.run(
            ["pgrep", "-f", "gunicorn"],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            logger.info("Servidor Gunicorn está em execução")
            return True
        else:
            logger.info("Servidor Gunicorn não está em execução")
            return False
    except Exception as e:
        logger.error(f"Erro ao verificar status do servidor: {e}")
        return False

def start_server():
    """Inicia o servidor Gunicorn"""
    try:
        logger.info("Iniciando servidor Gunicorn...")
        
        # Diretório da aplicação
        app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Comando para iniciar o Gunicorn
        cmd = [
            "gunicorn",
            "--bind=0.0.0.0:8080",
            "--workers=3",
            "--timeout=120",
            "--log-level=info",
            "--daemon",
            "wsgi:app"
        ]
        
        # Executa o comando
        subprocess.run(cmd, cwd=app_dir, check=True)
        
        # Aguarda um momento para o servidor iniciar
        time.sleep(3)
        
        if check_server_status():
            logger.info("Servidor iniciado com sucesso")
            return True
        else:
            logger.error("Falha ao iniciar o servidor")
            return False
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")
        return False

def stop_server():
    """Para o servidor Gunicorn"""
    try:
        logger.info("Parando servidor Gunicorn...")
        
        # Encontra os processos Gunicorn
        result = subprocess.run(
            ["pgrep", "-f", "gunicorn"],
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            logger.info("Nenhum processo Gunicorn em execução")
            return True
        
        # Envia sinal SIGTERM para os processos
        pids = result.stdout.strip().split('\n')
        for pid in pids:
            if pid:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    logger.info(f"Enviado sinal SIGTERM para PID {pid}")
                except Exception as e:
                    logger.error(f"Erro ao enviar sinal para PID {pid}: {e}")
        
        # Aguarda um momento para os processos encerrarem
        time.sleep(5)
        
        if not check_server_status():
            logger.info("Servidor parado com sucesso")
            return True
        else:
            logger.warning("Servidor ainda em execução após tentativa de parada")
            return False
    except Exception as e:
        logger.error(f"Erro ao parar servidor: {e}")
        return False

def restart_server():
    """Reinicia o servidor Gunicorn"""
    logger.info("Reiniciando servidor Gunicorn...")
    
    stop_server()
    return start_server()

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("Uso: python deploy.py [start|stop|restart|status]")
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        start_server()
    elif command == "stop":
        stop_server()
    elif command == "restart":
        restart_server()
    elif command == "status":
        check_server_status()
    else:
        print(f"Comando desconhecido: {command}")
        print("Uso: python deploy.py [start|stop|restart|status]")

if __name__ == "__main__":
    main()
