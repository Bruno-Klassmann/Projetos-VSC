/**
 * Classe para formatação de números e valores monetários
 * Lida com diferentes formatos de entrada e saída
 */
class NumberFormatter {
    /**
     * Inicializa o formatador de números
     * @param {string} locale - Localidade para formatação (ex: 'pt-BR', 'en-US')
     */
    constructor(locale = 'pt-BR') {
        this.locale = locale;
        this.currencyFormatter = new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        
        this.numberFormatter = new Intl.NumberFormat(locale, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    
    /**
     * Formata um valor como moeda
     * @param {number|string} value - Valor a ser formatado
     * @returns {string} - Valor formatado como moeda
     */
    formatCurrency(value) {
        // Se o valor for string, tenta converter para número
        if (typeof value === 'string') {
            value = this.parseNumber(value);
        }
        
        // Se não for um número válido, retorna 'N/A'
        if (value === null || isNaN(value) || value === Infinity) {
            return 'N/A';
        }
        
        return this.currencyFormatter.format(value);
    }
    
    /**
     * Formata um valor como número
     * @param {number|string} value - Valor a ser formatado
     * @returns {string} - Valor formatado como número
     */
    formatNumber(value) {
        // Se o valor for string, tenta converter para número
        if (typeof value === 'string') {
            value = this.parseNumber(value);
        }
        
        // Se não for um número válido, retorna 'N/A'
        if (value === null || isNaN(value) || value === Infinity) {
            return 'N/A';
        }
        
        return this.numberFormatter.format(value);
    }
    
    /**
     * Converte uma string de preço para número
     * Suporta diferentes formatos (BR, US, EU)
     * @param {string} priceStr - String de preço a ser convertida
     * @returns {number|null} - Valor numérico ou null se inválido
     */
    parseNumber(priceStr) {
        if (!priceStr || typeof priceStr !== 'string') {
            return null;
        }
        
        try {
            // Remove símbolos de moeda e espaços extras
            let cleanStr = priceStr.replace(/[R$\$€£\s]/g, '').trim();
            
            // Remove texto adicional (ex: "à vista", "no pix")
            cleanStr = cleanStr.split(/\s+(a partir de|à vista|no pix)/i)[0];
            
            // Identifica o formato com base nos separadores
            const lastComma = cleanStr.lastIndexOf(',');
            const lastDot = cleanStr.lastIndexOf('.');
            
            let result;
            
            if (lastComma > lastDot) {
                // Formato brasileiro/europeu: 1.234,56
                result = parseFloat(cleanStr.replace(/\./g, '').replace(',', '.'));
            } else if (lastDot > lastComma) {
                // Formato americano: 1,234.56
                result = parseFloat(cleanStr.replace(/,/g, ''));
            } else {
                // Sem separador decimal ou apenas um tipo
                // Tenta converter diretamente
                result = parseFloat(cleanStr.replace(',', '.'));
            }
            
            return isNaN(result) ? null : result;
        } catch (e) {
            console.error('Erro ao converter preço:', e);
            return null;
        }
    }
}
