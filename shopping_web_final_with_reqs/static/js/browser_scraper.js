/**
 * Browser Scraper - Módulo para realizar scraping diretamente no navegador
 * 
 * Este módulo implementa a funcionalidade de scraping no navegador do usuário,
 * utilizando técnicas como fetch API, CORS proxy e manipulação do DOM.
 * 
 * Versão corrigida para resolver problemas com Google Shopping, Kabum, links de compra
 * e formatação de preços
 */

class BrowserScraper {
    constructor() {
        // URL base para o proxy CORS no backend
        this.proxyUrl = '/api/proxy';
        
        // Headers padrão para simular um navegador normal
        this.headers = {
            'User-Agent': navigator.userAgent,
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        };
        
        // Status da busca atual
        this.searchStatus = {
            googleShopping: 'pending',
            mercadoLivre: 'pending',
            kabum: 'pending'
        };
        
        // Resultados da busca
        this.searchResults = [];
        
        // Debug mode
        this.debug = true;
    }
    
    /**
     * Realiza a busca em todos os sites
     * @param {string} query - Termo de busca
     * @param {function} progressCallback - Callback para atualizar o progresso
     * @returns {Promise<Array>} - Resultados da busca
     */
    async searchAllSites(query, progressCallback) {
        if (!query || query.trim() === '') {
            throw new Error('Termo de busca não pode ser vazio');
        }
        
        // Reinicia o status e os resultados
        this.searchStatus = {
            googleShopping: 'pending',
            mercadoLivre: 'pending',
            kabum: 'pending'
        };
        this.searchResults = [];
        
        // Atualiza o progresso inicial
        if (progressCallback) {
            progressCallback({
                status: 'iniciando',
                progress: 0,
                message: 'Iniciando busca em todos os sites...'
            });
        }
        
        // Inicia as buscas em paralelo
        const promises = [
            this.searchGoogleShopping(query, progressCallback),
            this.searchMercadoLivre(query, progressCallback),
            this.searchKabum(query, progressCallback)
        ];
        
        // Aguarda todas as buscas terminarem
        await Promise.allSettled(promises);
        
        // Atualiza o progresso final
        if (progressCallback) {
            progressCallback({
                status: 'concluido',
                progress: 100,
                message: 'Busca concluída em todos os sites'
            });
        }
        
        return this.searchResults;
    }
    
    /**
     * Realiza a busca no Google Shopping
     * @param {string} query - Termo de busca
     * @param {function} progressCallback - Callback para atualizar o progresso
     * @returns {Promise<Array>} - Resultados da busca
     */
    async searchGoogleShopping(query, progressCallback) {
        try {
            if (progressCallback) {
                progressCallback({
                    status: 'buscando',
                    site: 'Google Shopping',
                    progress: 33,
                    message: 'Buscando no Google Shopping...'
                });
            }
            
            this.searchStatus.googleShopping = 'searching';
            
            // Formata a query para URL
            const encodedQuery = encodeURIComponent(query);
            const url = `https://www.google.com/search?q=${encodedQuery}&tbm=shop`;
            
            // Faz a requisição através do proxy CORS
            const response = await fetch(`${this.proxyUrl}?url=${encodeURIComponent(url)}`);
            
            if (!response.ok) {
                throw new Error(`Erro ao buscar no Google Shopping: ${response.statusText}`);
            }
            
            const html = await response.text();
            
            // Cria um DOM parser para analisar o HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Log para debug
            if (this.debug) {
                console.log('Google Shopping HTML:', html.substring(0, 1000) + '...');
            }
            
            // Extrai os resultados usando múltiplos seletores para maior robustez
            let productElements = doc.querySelectorAll('div.sh-dgr__content');
            
            // Seletores alternativos se o primeiro falhar
            if (!productElements || productElements.length === 0) {
                productElements = doc.querySelectorAll('div.sh-dlr__list-result');
            }
            
            if (!productElements || productElements.length === 0) {
                productElements = doc.querySelectorAll('div.sh-pr__product-results-grid div.sh-pr__product-result');
            }
            
            const results = [];
            
            for (let i = 0; i < Math.min(productElements.length, 5); i++) {
                const element = productElements[i];
                
                try {
                    // Tenta múltiplos seletores para o nome
                    let nameElement = element.querySelector('h3.tAxDx');
                    if (!nameElement) nameElement = element.querySelector('h4.A2sOrd');
                    if (!nameElement) nameElement = element.querySelector('div.aULzUe');
                    if (!nameElement) nameElement = element.querySelector('h3');
                    
                    const name = nameElement ? nameElement.textContent.trim() : 'Nome não encontrado';
                    
                    // Tenta múltiplos seletores para o preço
                    let priceElement = element.querySelector('span.a8Pemb');
                    if (!priceElement) priceElement = element.querySelector('span.kHxwFf');
                    if (!priceElement) priceElement = element.querySelector('span[aria-hidden="true"]');
                    
                    const priceText = priceElement ? priceElement.textContent.trim() : 'Preço não encontrado';
                    const price = this.formatPrice(priceText);
                    
                    // Tenta múltiplos seletores para o link
                    let linkElement = element.querySelector('a.shntl');
                    if (!linkElement) linkElement = element.querySelector('a.Lq5OHe');
                    if (!linkElement) linkElement = element.querySelector('a');
                    
                    let link = linkElement ? linkElement.href : null;
                    
                    // Se o link for relativo, converte para absoluto
                    if (link && link.startsWith('/')) {
                        link = 'https://www.google.com' + link;
                    }
                    
                    // Extrai o link real do produto (não o link do Google)
                    const realProductLink = this.extractRealProductLink(link);
                    
                    if (price) {
                        results.push({
                            nome: name,
                            preco: price,
                            link: realProductLink || link,
                            site: 'Google Shopping'
                        });
                    }
                } catch (error) {
                    console.error('Erro ao extrair produto do Google Shopping:', error);
                }
            }
            
            // Adiciona os resultados à lista geral
            this.searchResults = this.searchResults.concat(results);
            
            this.searchStatus.googleShopping = 'completed';
            
            if (progressCallback) {
                progressCallback({
                    status: 'concluido',
                    site: 'Google Shopping',
                    progress: 33,
                    message: `Encontrados ${results.length} produtos no Google Shopping`
                });
            }
            
            return results;
        } catch (error) {
            console.error('Erro ao buscar no Google Shopping:', error);
            this.searchStatus.googleShopping = 'error';
            
            if (progressCallback) {
                progressCallback({
                    status: 'erro',
                    site: 'Google Shopping',
                    progress: 33,
                    message: `Erro ao buscar no Google Shopping: ${error.message}`
                });
            }
            
            return [];
        }
    }
    
    /**
     * Extrai o link real do produto a partir do link do Google Shopping
     * @param {string} googleLink - Link do Google Shopping
     * @returns {string|null} - Link real do produto ou null
     */
    extractRealProductLink(googleLink) {
        if (!googleLink) return null;
        
        try {
            // Tenta extrair o link real do produto da URL do Google
            const url = new URL(googleLink);
            const params = new URLSearchParams(url.search);
            
            // O Google armazena o link real em diferentes parâmetros
            const possibleParams = ['url', 'q', 'adurl'];
            
            for (const param of possibleParams) {
                if (params.has(param)) {
                    const realUrl = params.get(param);
                    if (realUrl && (realUrl.startsWith('http://') || realUrl.startsWith('https://'))) {
                        return realUrl;
                    }
                }
            }
        } catch (e) {
            console.warn('Erro ao extrair link real:', e);
        }
        
        return googleLink;
    }
    
    /**
     * Realiza a busca no Mercado Livre
     * @param {string} query - Termo de busca
     * @param {function} progressCallback - Callback para atualizar o progresso
     * @returns {Promise<Array>} - Resultados da busca
     */
    async searchMercadoLivre(query, progressCallback) {
        try {
            if (progressCallback) {
                progressCallback({
                    status: 'buscando',
                    site: 'Mercado Livre',
                    progress: 66,
                    message: 'Buscando no Mercado Livre...'
                });
            }
            
            this.searchStatus.mercadoLivre = 'searching';
            
            // Formata a query para URL
            const encodedQuery = encodeURIComponent(query);
            const url = `https://lista.mercadolivre.com.br/${encodedQuery}`;
            
            // Faz a requisição através do proxy CORS
            const response = await fetch(`${this.proxyUrl}?url=${encodeURIComponent(url)}`);
            
            if (!response.ok) {
                throw new Error(`Erro ao buscar no Mercado Livre: ${response.statusText}`);
            }
            
            const html = await response.text();
            
            // Cria um DOM parser para analisar o HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Log para debug
            if (this.debug) {
                console.log('Mercado Livre HTML:', html.substring(0, 1000) + '...');
            }
            
            // Extrai os resultados usando múltiplos seletores para maior robustez
            let productElements = doc.querySelectorAll('li.ui-search-layout__item');
            
            // Seletores alternativos se o primeiro falhar
            if (!productElements || productElements.length === 0) {
                productElements = doc.querySelectorAll('div.ui-search-result');
            }
            
            if (!productElements || productElements.length === 0) {
                productElements = doc.querySelectorAll('div.andes-card');
            }
            
            const results = [];
            
            for (let i = 0; i < Math.min(productElements.length, 5); i++) {
                const element = productElements[i];
                
                try {
                    // Tenta múltiplos seletores para o nome
                    let nameElement = element.querySelector('h2.ui-search-item__title');
                    if (!nameElement) nameElement = element.querySelector('h2.ui-search-result__title');
                    if (!nameElement) nameElement = element.querySelector('h2');
                    
                    const name = nameElement ? nameElement.textContent.trim() : 'Nome não encontrado';
                    
                    // Tenta múltiplos seletores para o preço
                    let priceElement = element.querySelector('span.andes-money-amount__fraction');
                    if (!priceElement) priceElement = element.querySelector('span.price-tag-fraction');
                    if (!priceElement) priceElement = element.querySelector('span.price-tag');
                    
                    let priceText = priceElement ? priceElement.textContent.trim() : '0';
                    
                    // Verifica se há centavos
                    let centsElement = element.querySelector('span.andes-money-amount__cents');
                    if (!centsElement) centsElement = element.querySelector('span.price-tag-cents');
                    
                    if (centsElement) {
                        const cents = centsElement.textContent.trim();
                        priceText = `${priceText},${cents}`;
                    }
                    
                    const price = this.formatPrice(priceText);
                    
                    // Tenta múltiplos seletores para o link
                    let linkElement = element.querySelector('a.ui-search-link');
                    if (!linkElement) linkElement = element.querySelector('a.ui-search-result__content');
                    if (!linkElement) linkElement = element.querySelector('a');
                    
                    const link = linkElement ? linkElement.href : null;
                    
                    // Gera o link do carrinho
                    const cartLink = this.generateMercadoLivreCartLink(link);
                    
                    if (price) {
                        results.push({
                            nome: name,
                            preco: price,
                            link: link,
                            cart_link: cartLink,
                            site: 'Mercado Livre'
                        });
                    }
                } catch (error) {
                    console.error('Erro ao extrair produto do Mercado Livre:', error);
                }
            }
            
            // Adiciona os resultados à lista geral
            this.searchResults = this.searchResults.concat(results);
            
            this.searchStatus.mercadoLivre = 'completed';
            
            if (progressCallback) {
                progressCallback({
                    status: 'concluido',
                    site: 'Mercado Livre',
                    progress: 66,
                    message: `Encontrados ${results.length} produtos no Mercado Livre`
                });
            }
            
            return results;
        } catch (error) {
            console.error('Erro ao buscar no Mercado Livre:', error);
            this.searchStatus.mercadoLivre = 'error';
            
            if (progressCallback) {
                progressCallback({
                    status: 'erro',
                    site: 'Mercado Livre',
                    progress: 66,
                    message: `Erro ao buscar no Mercado Livre: ${error.message}`
                });
            }
            
            return [];
        }
    }
    
    /**
     * Gera um link direto para o carrinho do Mercado Livre
     * @param {string} productUrl - URL do produto
     * @returns {string|null} - URL do carrinho
     */
    generateMercadoLivreCartLink(productUrl) {
        if (!productUrl) return null;
        
        try {
            // Extrai o ID do produto da URL
            const match = productUrl.match(/MLB-(\d+)/);
            if (match && match[1]) {
                const productId = match[1];
                return `https://www.mercadolivre.com.br/checkout/cart/add?item.id=MLB${productId}&quantity=1`;
            }
            
            // Tenta outro formato de URL
            const urlObj = new URL(productUrl);
            const pathParts = urlObj.pathname.split('/');
            const lastPart = pathParts[pathParts.length - 1];
            
            if (lastPart && lastPart.includes('-')) {
                const idPart = lastPart.split('-').pop();
                if (idPart && /^\d+$/.test(idPart)) {
                    return `https://www.mercadolivre.com.br/checkout/cart/add?item.id=MLB${idPart}&quantity=1`;
                }
            }
            
            // Tenta extrair o ID do produto da URL completa
            const mlbMatch = productUrl.match(/MLB(\d+)/);
            if (mlbMatch && mlbMatch[1]) {
                return `https://www.mercadolivre.com.br/checkout/cart/add?item.id=MLB${mlbMatch[1]}&quantity=1`;
            }
        } catch (e) {
            console.warn('Erro ao gerar link do carrinho do Mercado Livre:', e);
        }
        
        // Se não conseguir extrair o ID, retorna o link do produto
        return productUrl;
    }
    
    /**
     * Realiza a busca na Kabum
     * @param {string} query - Termo de busca
     * @param {function} progressCallback - Callback para atualizar o progresso
     * @returns {Promise<Array>} - Resultados da busca
     */
    async searchKabum(query, progressCallback) {
        try {
            if (progressCallback) {
                progressCallback({
                    status: 'buscando',
                    site: 'Kabum',
                    progress: 100,
                    message: 'Buscando na Kabum...'
                });
            }
            
            this.searchStatus.kabum = 'searching';
            
            // Formata a query para URL
            const encodedQuery = encodeURIComponent(query);
            const url = `https://www.kabum.com.br/busca/${encodedQuery}`;
            
            // Faz a requisição através do proxy CORS
            const response = await fetch(`${this.proxyUrl}?url=${encodeURIComponent(url)}`);
            
            if (!response.ok) {
                throw new Error(`Erro ao buscar na Kabum: ${response.statusText}`);
            }
            
            const html = await response.text();
            
            // Cria um DOM parser para analisar o HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Log para debug
            if (this.debug) {
                console.log('Kabum HTML:', html.substring(0, 1000) + '...');
            }
            
            // Extrai os resultados usando múltiplos seletores para maior robustez
            let productElements = doc.querySelectorAll('div.productCard');
            
            // Seletores alternativos se o primeiro falhar
            if (!productElements || productElements.length === 0) {
                productElements = doc.querySelectorAll('div.sc-cdc9b13f-7');
            }
            
            if (!productElements || productElements.length === 0) {
                productElements = doc.querySelectorAll('div[data-testid="product-card"]');
            }
            
            if (!productElements || productElements.length === 0) {
                productElements = doc.querySelectorAll('div.cardProduct');
            }
            
            // Tenta extrair produtos do script JSON-LD
            let results = this.extractKabumProductsFromJsonLd(doc);
            
            // Se não encontrou produtos no JSON-LD, tenta extrair do HTML
            if (results.length === 0 && productElements.length > 0) {
                for (let i = 0; i < Math.min(productElements.length, 5); i++) {
                    const element = productElements[i];
                    
                    try {
                        // Tenta múltiplos seletores para o nome
                        let nameElement = element.querySelector('span.nameCard');
                        if (!nameElement) nameElement = element.querySelector('h2.sc-d79c9c3f-0');
                        if (!nameElement) nameElement = element.querySelector('h2');
                        if (!nameElement) nameElement = element.querySelector('span.sc-cdc9b13f-16');
                        
                        const name = nameElement ? nameElement.textContent.trim() : 'Nome não encontrado';
                        
                        // Tenta múltiplos seletores para o preço
                        let priceElement = element.querySelector('span.priceCard');
                        if (!priceElement) priceElement = element.querySelector('span.sc-3b515ca1-2');
                        if (!priceElement) priceElement = element.querySelector('span.sc-cdc9b13f-0');
                        
                        const priceText = priceElement ? priceElement.textContent.trim() : 'Preço não encontrado';
                        const price = this.formatPrice(priceText);
                        
                        // Tenta múltiplos seletores para o link
                        let linkElement = element.querySelector('a.productLink');
                        if (!linkElement) linkElement = element.querySelector('a.sc-cdc9b13f-10');
                        if (!linkElement) linkElement = element.querySelector('a');
                        
                        let link = linkElement ? linkElement.href : null;
                        
                        // Se o link for relativo, converte para absoluto
                        if (link && link.startsWith('/')) {
                            link = 'https://www.kabum.com.br' + link;
                        }
                        
                        // Gera o link do carrinho
                        const cartLink = this.generateKabumCartLink(link);
                        
                        if (price) {
                            results.push({
                                nome: name,
                                preco: price,
                                link: link,
                                cart_link: cartLink,
                                site: 'Kabum'
                            });
                        }
                    } catch (error) {
                        console.error('Erro ao extrair produto da Kabum:', error);
                    }
                }
            }
            
            // Adiciona os resultados à lista geral
            this.searchResults = this.searchResults.concat(results);
            
            this.searchStatus.kabum = 'completed';
            
            if (progressCallback) {
                progressCallback({
                    status: 'concluido',
                    site: 'Kabum',
                    progress: 100,
                    message: `Encontrados ${results.length} produtos na Kabum`
                });
            }
            
            return results;
        } catch (error) {
            console.error('Erro ao buscar na Kabum:', error);
            this.searchStatus.kabum = 'error';
            
            if (progressCallback) {
                progressCallback({
                    status: 'erro',
                    site: 'Kabum',
                    progress: 100,
                    message: `Erro ao buscar na Kabum: ${error.message}`
                });
            }
            
            return [];
        }
    }
    
    /**
     * Extrai produtos da Kabum a partir do script JSON-LD
     * @param {Document} doc - Documento HTML
     * @returns {Array} - Lista de produtos
     */
    extractKabumProductsFromJsonLd(doc) {
        try {
            const scripts = doc.querySelectorAll('script[type="application/ld+json"]');
            
            for (const script of scripts) {
                try {
                    const data = JSON.parse(script.textContent);
                    
                    // Verifica se é o JSON-LD de produtos
                    if (data && (data['@type'] === 'ItemList' || data['@type'] === 'Product' || 
                                (Array.isArray(data) && data.length > 0 && data[0]['@type'] === 'Product'))) {
                        
                        const products = [];
                        
                        // Caso seja um array de produtos
                        if (Array.isArray(data)) {
                            for (const item of data.slice(0, 5)) {
                                if (item['@type'] === 'Product') {
                                    products.push(this.parseKabumJsonLdProduct(item));
                                }
                            }
                        }
                        // Caso seja uma lista de itens
                        else if (data['@type'] === 'ItemList' && data.itemListElement) {
                            for (const item of data.itemListElement.slice(0, 5)) {
                                if (item.item && item.item['@type'] === 'Product') {
                                    products.push(this.parseKabumJsonLdProduct(item.item));
                                }
                            }
                        }
                        // Caso seja um único produto
                        else if (data['@type'] === 'Product') {
                            products.push(this.parseKabumJsonLdProduct(data));
                        }
                        
                        return products.filter(p => p !== null);
                    }
                } catch (e) {
                    console.warn('Erro ao analisar JSON-LD:', e);
                }
            }
        } catch (e) {
            console.warn('Erro ao extrair produtos do JSON-LD:', e);
        }
        
        return [];
    }
    
    /**
     * Analisa um produto da Kabum a partir do JSON-LD
     * @param {Object} product - Objeto do produto no JSON-LD
     * @returns {Object|null} - Produto formatado ou null
     */
    parseKabumJsonLdProduct(product) {
        try {
            if (!product.name || !product.offers) return null;
            
            let price = null;
            let link = product.url || null;
            
            // Extrai o preço
            if (product.offers.price) {
                price = parseFloat(product.offers.price);
            } else if (Array.isArray(product.offers) && product.offers.length > 0 && product.offers[0].price) {
                price = parseFloat(product.offers[0].price);
            }
            
            if (!price || isNaN(price) || !link) return null;
            
            // Gera o link do carrinho
            const cartLink = this.generateKabumCartLink(link);
            
            return {
                nome: product.name,
                preco: price,
                link: link,
                cart_link: cartLink,
                site: 'Kabum'
            };
        } catch (e) {
            console.warn('Erro ao analisar produto do JSON-LD:', e);
            return null;
        }
    }
    
    /**
     * Gera um link direto para o carrinho da Kabum
     * @param {string} productUrl - URL do produto
     * @returns {string|null} - URL do carrinho
     */
    generateKabumCartLink(productUrl) {
        if (!productUrl) return null;
        
        try {
            // Extrai o código do produto da URL
            const match = productUrl.match(/\/produto\/(\d+)/);
            if (match && match[1]) {
                const productCode = match[1];
                return `https://www.kabum.com.br/produto/${productCode}?buybox=true`;
            }
            
            // Tenta outro formato de URL
            const urlObj = new URL(productUrl);
            const pathParts = urlObj.pathname.split('/');
            
            // Procura por um segmento que seja apenas números
            for (const part of pathParts) {
                if (/^\d+$/.test(part)) {
                    return `https://www.kabum.com.br/produto/${part}?buybox=true`;
                }
            }
        } catch (e) {
            console.warn('Erro ao gerar link do carrinho da Kabum:', e);
        }
        
        // Se não conseguir extrair o código, retorna o link do produto
        return productUrl;
    }
    
    /**
     * Formata o preço para um valor numérico
     * @param {string} priceStr - String com o preço
     * @returns {number|null} - Preço formatado ou null se inválido
     */
    formatPrice(priceStr) {
        if (!priceStr) {
            return null;
        }
        
        try {
            // Log para debug
            if (this.debug) {
                console.log('Formatando preço:', priceStr);
            }
            
            // Remove caracteres não numéricos, mantendo pontos e vírgulas
            let cleanPrice = priceStr.replace(/[^\d,.]/g, '');
            
            // Log para debug
            if (this.debug) {
                console.log('Preço limpo:', cleanPrice);
            }
            
            // Trata diferentes formatos de preço
            if (cleanPrice.includes(',') && cleanPrice.includes('.')) {
                // Formato brasileiro com separador de milhar (ex: 1.234,56)
                // Remove pontos e substitui vírgula por ponto
                cleanPrice = cleanPrice.replace(/\./g, '').replace(',', '.');
            } else if (cleanPrice.includes(',')) {
                // Formato com vírgula como decimal (ex: 1234,56)
                cleanPrice = cleanPrice.replace(',', '.');
            }
            
            // Log para debug
            if (this.debug) {
                console.log('Preço normalizado:', cleanPrice);
            }
            
            // Converte para número
            const price = parseFloat(cleanPrice);
            
            // Log para debug
            if (this.debug) {
                console.log('Preço final:', price);
            }
            
            return isNaN(price) ? null : price;
        } catch (error) {
            console.warn('Erro ao formatar preço:', error);
            return null;
        }
    }
    
    /**
     * Tenta obter o link direto para adicionar ao carrinho
     * @param {string} productUrl - URL do produto
     * @param {string} site - Nome do site
     * @returns {string} - URL do carrinho
     */
    getCartLink(productUrl, site) {
        if (!productUrl) {
            return null;
        }
        
        switch (site) {
            case 'Mercado Livre':
                return this.generateMercadoLivreCartLink(productUrl);
            case 'Kabum':
                return this.generateKabumCartLink(productUrl);
            default:
                // Para outros sites, o link do produto já é suficiente
                return productUrl;
        }
    }
    
    /**
     * Encontra as melhores ofertas por site e a melhor oferta geral
     * @param {Array} results - Resultados da busca
     * @returns {Object} - Melhores ofertas
     */
    findBestDeals(results) {
        const bestDeals = {
            "Google Shopping": null,
            "Mercado Livre": null,
            "Kabum": null,
            "Melhor Oferta": null
        };
        
        // Agrupa por site
        for (const site of ["Google Shopping", "Mercado Livre", "Kabum"]) {
            const siteResults = results.filter(r => r.site === site);
            
            // Encontra o produto com menor preço para cada site
            if (siteResults.length > 0) {
                const bestDeal = siteResults.reduce((min, p) => p.preco < min.preco ? p : min, siteResults[0]);
                
                // Tenta obter o link do carrinho se não existir
                if (!bestDeal.cart_link) {
                    bestDeal.cart_link = this.getCartLink(bestDeal.link, site);
                }
                
                bestDeals[site] = bestDeal;
            }
        }
        
        // Encontra a melhor oferta geral (menor preço entre todos os sites)
        const validDeals = [
            bestDeals["Google Shopping"], 
            bestDeals["Mercado Livre"], 
            bestDeals["Kabum"]
        ].filter(deal => deal !== null);
        
        if (validDeals.length > 0) {
            const bestOverall = validDeals.reduce((min, p) => p.preco < min.preco ? p : min, validDeals[0]);
            bestDeals["Melhor Oferta"] = bestOverall;
        }
        
        return bestDeals;
    }
}

// Exporta a classe para uso global
window.BrowserScraper = BrowserScraper;
