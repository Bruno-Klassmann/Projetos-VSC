/**
 * Utilitário para tratamento de erros de UI
 * Centraliza funções para verificar elementos e exibir mensagens de erro
 */
class UIErrorHandler {
    /**
     * Verifica se um elemento existe e exibe mensagem de erro se não existir
     * @param {Element|null} element - Elemento a ser verificado
     * @param {string} elementName - Nome do elemento para mensagem de erro
     * @param {boolean} silent - Se verdadeiro, não exibe mensagem no console
     * @returns {boolean} - Verdadeiro se o elemento existe
     */
    static checkElement(element, elementName, silent = false) {
        if (!element) {
            if (!silent) {
                console.error(`Elemento ${elementName} não encontrado!`);
            }
            return false;
        }
        return true;
    }
    
    /**
     * Tenta definir o conteúdo de texto de um elemento com verificação de segurança
     * @param {Element|null} element - Elemento alvo
     * @param {string} value - Valor a ser definido
     * @param {string} elementName - Nome do elemento para mensagem de erro
     * @returns {boolean} - Verdadeiro se a operação foi bem-sucedida
     */
    static setTextContent(element, value, elementName) {
        if (!this.checkElement(element, elementName)) {
            return false;
        }
        
        try {
            element.textContent = value;
            return true;
        } catch (error) {
            console.error(`Erro ao definir texto para ${elementName}:`, error);
            return false;
        }
    }
    
    /**
     * Tenta definir um atributo de um elemento com verificação de segurança
     * @param {Element|null} element - Elemento alvo
     * @param {string} attribute - Nome do atributo
     * @param {string} value - Valor a ser definido
     * @param {string} elementName - Nome do elemento para mensagem de erro
     * @returns {boolean} - Verdadeiro se a operação foi bem-sucedida
     */
    static setAttribute(element, attribute, value, elementName) {
        if (!this.checkElement(element, elementName)) {
            return false;
        }
        
        try {
            element.setAttribute(attribute, value);
            return true;
        } catch (error) {
            console.error(`Erro ao definir atributo ${attribute} para ${elementName}:`, error);
            return false;
        }
    }
    
    /**
     * Tenta definir uma propriedade de estilo de um elemento com verificação de segurança
     * @param {Element|null} element - Elemento alvo
     * @param {string} property - Nome da propriedade de estilo
     * @param {string} value - Valor a ser definido
     * @param {string} elementName - Nome do elemento para mensagem de erro
     * @returns {boolean} - Verdadeiro se a operação foi bem-sucedida
     */
    static setStyle(element, property, value, elementName) {
        if (!this.checkElement(element, elementName)) {
            return false;
        }
        
        try {
            element.style[property] = value;
            return true;
        } catch (error) {
            console.error(`Erro ao definir estilo ${property} para ${elementName}:`, error);
            return false;
        }
    }
    
    /**
     * Tenta adicionar um evento a um elemento com verificação de segurança
     * @param {Element|null} element - Elemento alvo
     * @param {string} eventType - Tipo de evento (ex: 'click')
     * @param {Function} handler - Função de tratamento do evento
     * @param {string} elementName - Nome do elemento para mensagem de erro
     * @returns {boolean} - Verdadeiro se a operação foi bem-sucedida
     */
    static addEventListener(element, eventType, handler, elementName) {
        if (!this.checkElement(element, elementName)) {
            return false;
        }
        
        try {
            element.addEventListener(eventType, handler);
            return true;
        } catch (error) {
            console.error(`Erro ao adicionar evento ${eventType} para ${elementName}:`, error);
            return false;
        }
    }
    
    /**
     * Verifica se um objeto tem uma propriedade específica
     * @param {Object|null} obj - Objeto a ser verificado
     * @param {string} property - Nome da propriedade
     * @param {string} objectName - Nome do objeto para mensagem de erro
     * @returns {boolean} - Verdadeiro se o objeto tem a propriedade
     */
    static hasProperty(obj, property, objectName) {
        if (!obj) {
            console.error(`Objeto ${objectName} é nulo ou indefinido!`);
            return false;
        }
        
        if (!(property in obj)) {
            console.error(`Propriedade ${property} não encontrada em ${objectName}!`);
            return false;
        }
        
        return true;
    }
}
