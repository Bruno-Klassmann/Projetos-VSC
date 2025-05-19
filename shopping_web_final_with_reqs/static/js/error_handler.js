/**
 * Classe para tratamento de erros do scraper
 * Centraliza o tratamento de erros e logging
 */
class ScraperErrorHandler {
    constructor() {
        this.errors = [];
        this.maxErrors = 100; // Limite para evitar consumo excessivo de memória
    }

    /**
     * Registra um erro
     * @param {string} module - Módulo onde ocorreu o erro
     * @param {string} method - Método onde ocorreu o erro
     * @param {Error} error - Objeto de erro
     */
    logError(module, method, error) {
        console.error(`[${module}:${method}] ${error.message}`, error);
        
        // Adiciona o erro ao histórico
        this.errors.push({
            timestamp: new Date().toISOString(),
            module,
            method,
            message: error.message,
            stack: error.stack
        });
        
        // Limita o tamanho do histórico
        if (this.errors.length > this.maxErrors) {
            this.errors.shift();
        }
        
        // Envia o erro para o servidor (opcional)
        this.reportErrorToServer(module, method, error).catch(e => {
            console.error("Falha ao reportar erro:", e);
        });
        
        return error; // Retorna o erro para permitir encadeamento
    }
    
    /**
     * Reporta o erro para o servidor para análise
     * @param {string} module - Módulo onde ocorreu o erro
     * @param {string} method - Método onde ocorreu o erro
     * @param {Error} error - Objeto de erro
     */
    async reportErrorToServer(module, method, error) {
        try {
            // Implementação opcional - enviar erros para o servidor
            // para análise e depuração
            /*
            await fetch('/api/log-error', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    timestamp: new Date().toISOString(),
                    module,
                    method,
                    message: error.message,
                    stack: error.stack,
                    userAgent: navigator.userAgent
                })
            });
            */
        } catch (e) {
            // Silencia erros no reporte para evitar loops
            console.error("Erro ao reportar erro:", e);
        }
    }
    
    /**
     * Obtém o histórico de erros
     * @returns {Array} - Lista de erros registrados
     */
    getErrorHistory() {
        return [...this.errors];
    }
    
    /**
     * Limpa o histórico de erros
     */
    clearErrorHistory() {
        this.errors = [];
    }
    
    /**
     * Verifica se um determinado tipo de erro ocorreu recentemente
     * @param {string} errorType - Parte da mensagem de erro a procurar
     * @param {number} timeWindowMs - Janela de tempo em milissegundos
     * @returns {boolean} - Verdadeiro se o erro ocorreu na janela de tempo
     */
    hasErrorOccurredRecently(errorType, timeWindowMs = 60000) {
        const now = new Date();
        return this.errors.some(error => {
            const errorTime = new Date(error.timestamp);
            const timeDiff = now - errorTime;
            return timeDiff <= timeWindowMs && error.message.includes(errorType);
        });
    }
}
