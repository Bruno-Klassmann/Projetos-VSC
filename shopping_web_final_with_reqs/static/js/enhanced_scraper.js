/**
 * Extensão do BrowserScraper para suportar a nova arquitetura híbrida
 * 
 * Este módulo modifica o scraper do navegador para trabalhar com a nova
 * abordagem onde o Google Shopping é processado no servidor e os outros
 * sites continuam sendo processados no navegador.
 */

// Estende a classe BrowserScraper com funcionalidades adicionais
class EnhancedBrowserScraper extends BrowserScraper {
    constructor() {
        super();
        
        // Configurações adicionais
        this.maxRetries = 2; // Número máximo de tentativas para cada site
        this.retryDelay = 1000; // Tempo de espera entre tentativas (ms)
        
        // Estatísticas de scraping
        this.stats = {
            startTime: null,
            endTime: null,
            totalProducts: 0,
            siteStats: {
                "Google Shopping": { attempts: 0, success: false, products: 0 },
                "Mercado Livre": { attempts: 0, success: false, products: 0 },
                "Kabum": { attempts: 0, success: false, products: 0 }
            }
        };
    }
    
    /**
     * Realiza a busca apenas no Mercado Livre e Kabum
     * (Google Shopping agora é processado no servidor)
     * @param {string} query - Termo de busca
     * @param {function} progressCallback - Callback para atualizar o progresso
     * @returns {Promise<Array>} - Resultados da busca
     */
    async searchOtherSites(query, progressCallback) {
        if (!query || query.trim() === '') {
            throw new Error('Termo de busca não pode ser vazio');
        }
        
        // Reinicia estatísticas
        this.stats.startTime = new Date();
        this.stats.totalProducts = 0;
        Object.keys(this.stats.siteStats).forEach(site => {
            this.stats.siteStats[site] = { attempts: 0, success: false, products: 0 };
        });
        
        // Reinicia o status e os resultados
        this.searchStatus = {
            mercadoLivre: 'pending',
            kabum: 'pending'
        };
        this.searchResults = [];
        
        // Inicia as buscas em paralelo com suporte a retentativas
        const promises = [
            this.searchWithRetry('Mercado Livre', query, progressCallback),
            this.searchWithRetry('Kabum', query, progressCallback)
        ];
        
        // Aguarda todas as buscas terminarem
        const results = await Promise.all(promises);
        
        // Registra o tempo de término
        this.stats.endTime = new Date();
        this.stats.totalProducts = this.searchResults.length;
        
        // Combina os resultados
        const allResults = results.flat();
        
        return allResults;
    }
    
    /**
     * Realiza a busca em um site específico com suporte a retentativas
     * @param {string} site - Nome do site
     * @param {string} query - Termo de busca
     * @param {function} progressCallback - Callback para atualizar o progresso
     * @returns {Promise<Array>} - Resultados da busca
     */
    async searchWithRetry(site, query, progressCallback) {
        let attempt = 0;
        let results = [];
        let success = false;
        
        // Mapeia o nome do site para a função de busca correspondente
        const searchFunctions = {
            'Mercado Livre': this.searchMercadoLivre.bind(this),
            'Kabum': this.searchKabum.bind(this)
        };
        
        const searchFunction = searchFunctions[site];
        if (!searchFunction) {
            throw new Error(`Site não suportado: ${site}`);
        }
        
        // Tenta a busca até o número máximo de tentativas
        while (attempt < this.maxRetries && !success) {
            attempt++;
            this.stats.siteStats[site].attempts = attempt;
            
            try {
                if (progressCallback && attempt > 1) {
                    progressCallback({
                        status: 'buscando',
                        site: site,
                        progress: this.getProgressForSite(site),
                        message: `Tentativa ${attempt}/${this.maxRetries} no ${site}...`
                    });
                }
                
                // Executa a busca
                results = await searchFunction(query, progressCallback);
                
                // Verifica se os resultados têm links para o carrinho
                results = this.ensureCartLinks(results, site);
                
                // Se chegou aqui, a busca foi bem-sucedida
                success = true;
                this.stats.siteStats[site].success = true;
                this.stats.siteStats[site].products = results.length;
                
                if (progressCallback) {
                    progressCallback({
                        status: 'concluido',
                        site: site,
                        progress: this.getProgressForSite(site),
                        message: `Encontrados ${results.length} produtos no ${site}`
                    });
                }
                
                return results;
            } catch (error) {
                console.error(`Erro na tentativa ${attempt} para ${site}:`, error);
                
                // Se não for a última tentativa, aguarda antes de tentar novamente
                if (attempt < this.maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, this.retryDelay));
                } else {
                    // Na última tentativa, reporta o erro
                    if (progressCallback) {
                        progressCallback({
                            status: 'erro',
                            site: site,
                            progress: this.getProgressForSite(site),
                            message: `Erro ao buscar no ${site} após ${attempt} tentativas: ${error.message}`
                        });
                    }
                }
            }
        }
        
        // Se todas as tentativas falharam, retorna uma lista vazia
        return [];
    }
    
    /**
     * Garante que todos os resultados tenham links para o carrinho
     * @param {Array} results - Resultados da busca
     * @param {string} site - Nome do site
     * @returns {Array} - Resultados com links para o carrinho
     */
    ensureCartLinks(results, site) {
        return results.map(product => {
            if (!product.cart_link && product.link) {
                // Adiciona link para o carrinho se não existir
                switch (site) {
                    case 'Mercado Livre':
                        product.cart_link = this.generateMercadoLivreCartLink(product.link);
                        break;
                    case 'Kabum':
                        product.cart_link = this.generateKabumCartLink(product.link);
                        break;
                    default:
                        product.cart_link = product.link;
                }
            }
            return product;
        });
    }
    
    /**
     * Calcula o progresso para um site específico
     * @param {string} site - Nome do site
     * @returns {number} - Valor do progresso (0-100)
     */
    getProgressForSite(site) {
        const siteProgress = {
            'Mercado Livre': 66,
            'Kabum': 100
        };
        
        return siteProgress[site] || 0;
    }
    
    /**
     * Obtém estatísticas da última busca
     * @returns {Object} - Estatísticas de scraping
     */
    getScrapingStats() {
        if (!this.stats.endTime) {
            return {
                status: 'Nenhuma busca realizada ainda',
                stats: this.stats
            };
        }
        
        const duration = (this.stats.endTime - this.stats.startTime) / 1000;
        
        return {
            status: 'Busca concluída',
            duration: `${duration.toFixed(1)} segundos`,
            totalProducts: this.stats.totalProducts,
            siteStats: this.stats.siteStats
        };
    }
}

// Substitui a classe original pela versão aprimorada
window.BrowserScraper = EnhancedBrowserScraper;
