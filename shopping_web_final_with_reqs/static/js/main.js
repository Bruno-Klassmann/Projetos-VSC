// Elementos principais
const searchInput = document.getElementById("search-input");
const searchButton = document.getElementById("search-button");
const searchStatus = document.getElementById("search-status");
const resultsSection = document.getElementById("results-section");
const recentList = document.getElementById("recent-list");

// Templates
const dealCardTemplate = document.getElementById("deal-card-template");
const recentSearchItemTemplate = document.getElementById("recent-search-item-template");

// Estado da aplicação
let currentResults = null;
let errorHandler = null;
let numberFormatter = null;

// Inicialização
document.addEventListener("DOMContentLoaded", () => {
    // Inicializa o tratador de erros
    errorHandler = new ScraperErrorHandler();
    
    // Inicializa o formatador de números
    numberFormatter = new NumberFormatter("pt-BR");
    
    // Carregar buscas recentes
    loadRecentSearches();
    
    // Configurar eventos
    UIErrorHandler.addEventListener(searchButton, "click", handleSearch, "searchButton");
    UIErrorHandler.addEventListener(searchInput, "keypress", (e) => {
        if (e.key === "Enter") {
            handleSearch();
        }
    }, "searchInput");
});

// Função para realizar a busca
async function handleSearch() {
    const query = searchInput.value.trim();
    
    if (!query) {
        showStatus("Por favor, digite um produto para buscar.", "error");
        return;
    }
    
    // Mostrar status de carregamento inicial
    showStatus("<div class=\"spinner\"></div> Buscando as melhores ofertas no Google Shopping...", "loading");
    
    try {
        // Limpar seção de resultados anterior
        const topDealsContainer = document.getElementById("top-deals");
        if (UIErrorHandler.checkElement(topDealsContainer, "topDealsContainer")) {
            topDealsContainer.innerHTML = ""; // Limpa apenas as ofertas anteriores
        }
        UIErrorHandler.setStyle(resultsSection, "display", "none", "resultsSection");
        
        // Busca as melhores ofertas no Google Shopping
        const topDeals = await searchTopDeals(query);
        
        // Formatar os resultados
        const formattedResults = formatResults(topDeals, query);
        
        // Salvar resultados atuais
        currentResults = formattedResults;
        
        // Exibir resultados
        displayResults(formattedResults);
        
        // Salvar resultados no backend
        await saveResultsToBackend(formattedResults);
        
        // Atualizar buscas recentes
        loadRecentSearches();
        
    } catch (error) {
        errorHandler.logError("Main", "handleSearch", error);
        showStatus(`Erro na busca: ${error.message}`, "error");
        console.error("Erro na busca:", error);
    }
}

// Função para buscar as melhores ofertas no Google Shopping
async function searchTopDeals(query) {
    try {
        // Faz a requisição para a API do servidor
        const response = await fetch(`/api/search/top-deals?query=${encodeURIComponent(query)}`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: response.statusText }));
            throw new Error(`Erro ${response.status}: ${errorData.error || "Falha na API"}`);
        }
        
        return await response.json();
    } catch (error) {
        errorHandler.logError("GoogleShopping", "searchTopDeals", error);
        console.error("Erro ao buscar melhores ofertas:", error);
        showStatus(`Erro ao buscar no Google Shopping: ${error.message}`, "error");
        throw error;
    }
}

// Função para formatar os resultados
function formatResults(data, query) {
    const timestamp = new Date().toLocaleString("pt-BR");
    
    // Se a query não estiver nos dados, usa a fornecida
    if (!data.query) {
        data.query = query;
    }
    
    // Se o timestamp não estiver nos dados, usa o atual
    if (!data.timestamp) {
        data.timestamp = timestamp;
    }
    
    // Formata os preços dos produtos
    if (data.top_deals && Array.isArray(data.top_deals)) {
        data.top_deals = data.top_deals.map(deal => ({
            ...deal,
            preco_formatado: formatCurrency(deal.preco)
        }));
    }
    
    return data;
}

/**
 * Formata um valor numérico como moeda brasileira (R$)
 * @param {number} value - Valor a ser formatado
 * @returns {string} - Valor formatado como moeda
 */
function formatCurrency(value) {
    return numberFormatter.formatCurrency(value);
}

// Função para exibir os resultados
function displayResults(data) {
    // Seleciona os elementos para query e timestamp diretamente na seção de resultados
    const queryTextElement = resultsSection.querySelector(".query-text");
    const timestampTextElement = resultsSection.querySelector(".timestamp-text");

    // Usa UIErrorHandler para definir o conteúdo com segurança
    UIErrorHandler.setTextContent(queryTextElement, data.query, ".query-text");
    UIErrorHandler.setTextContent(timestampTextElement, data.timestamp, ".timestamp-text");
    
    // Exibir as melhores ofertas
    const topDealsContainer = document.getElementById("top-deals");
    
    if (!UIErrorHandler.checkElement(topDealsContainer, "#top-deals")) {
        showStatus("Erro interno: Falha ao encontrar o container de resultados.", "error");
        return;
    }
    
    // Limpar container de ofertas
    topDealsContainer.innerHTML = "";
    
    if (data.top_deals && Array.isArray(data.top_deals) && data.top_deals.length > 0) {
        // Adicionar título e botão de exportação
        const headerDiv = document.createElement("div");
        headerDiv.className = "top-deals-header";
        
        const titleElement = document.createElement("h3");
        titleElement.textContent = "As 3 Melhores Ofertas no Google Shopping";
        titleElement.className = "top-deals-title";
        headerDiv.appendChild(titleElement);
        
        // Adicionar botão de exportação para XLSX
        const exportButton = document.createElement("button");
        exportButton.textContent = "Exportar para Excel";
        exportButton.className = "btn btn-export";
        exportButton.addEventListener("click", () => exportToXLSX(data));
        headerDiv.appendChild(exportButton);
        
        topDealsContainer.appendChild(headerDiv);
        
        // Adicionar cada oferta
        data.top_deals.forEach((deal, index) => {
            if (!dealCardTemplate) {
                console.error("Template deal-card-template não encontrado!");
                return;
            }
            const dealElement = dealCardTemplate.content.cloneNode(true);
            
            // Seleciona elementos dentro do card clonado
            const rankElement = dealElement.querySelector(".deal-rank");
            const nameElement = dealElement.querySelector(".product-name");
            const priceElement = dealElement.querySelector(".price");
            const cartLink = dealElement.querySelector(".cart-link");
            
            // Usa UIErrorHandler para definir o conteúdo com segurança
            UIErrorHandler.setTextContent(rankElement, `#${index + 1}`, ".deal-rank");
            UIErrorHandler.setTextContent(nameElement, deal.nome, ".product-name");
            UIErrorHandler.setTextContent(priceElement, deal.preco_formatado || formatCurrency(deal.preco), ".price");
            
            if (UIErrorHandler.checkElement(cartLink, ".cart-link")) {
                if (deal.cart_link || deal.link) {
                    UIErrorHandler.setAttribute(cartLink, "href", deal.cart_link || deal.link, ".cart-link");
                } else {
                    UIErrorHandler.setStyle(cartLink, "display", "none", ".cart-link");
                }
            }
            
            topDealsContainer.appendChild(dealElement);
        });
    } else {
        topDealsContainer.innerHTML = "<p>Nenhuma oferta encontrada para esta busca.</p>";
    }
    
    // Exibir seção de resultados
    UIErrorHandler.setStyle(resultsSection, "display", "block", "resultsSection");
    resultsSection.scrollIntoView({ behavior: "smooth" });
    
    // Limpar status após exibir resultados
    showStatus("");
}

// Função para exportar resultados para XLSX
async function exportToXLSX(data) {
    try {
        showStatus("<div class=\"spinner\"></div> Gerando arquivo Excel...", "loading");
        
        const response = await fetch('/api/export-xlsx', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: response.statusText }));
            throw new Error(`Erro ${response.status}: ${errorData.error || "Falha ao exportar"}`);
        }
        
        // Obter o blob do arquivo
        const blob = await response.blob();
        
        // Criar URL para o blob
        const url = window.URL.createObjectURL(blob);
        
        // Criar link temporário para download
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        // Extrair nome do arquivo do cabeçalho Content-Disposition, se disponível
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'melhores_ofertas.xlsx';
        
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?([^"]*)"?/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1];
            }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        
        // Limpar
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showStatus("Arquivo Excel gerado com sucesso!", "success");
        
        // Limpar status após alguns segundos
        setTimeout(() => {
            showStatus("");
        }, 3000);
        
    } catch (error) {
        errorHandler.logError("Main", "exportToXLSX", error);
        showStatus(`Erro ao exportar para Excel: ${error.message}`, "error");
        console.error("Erro ao exportar para Excel:", error);
    }
}

// Função para salvar os resultados no backend
async function saveResultsToBackend(results) {
    try {
        const response = await fetch("/api/save-results", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(results)
        });
        
        if (!response.ok) {
            throw new Error("Erro ao salvar resultados");
        }
        
        return await response.json();
    } catch (error) {
        errorHandler.logError("Main", "saveResultsToBackend", error);
        console.error("Erro ao salvar resultados:", error);
        // Não interrompe o fluxo se falhar ao salvar
        return null;
    }
}

// Função para carregar buscas recentes
async function loadRecentSearches() {
    try {
        // Limpar lista
        if (!UIErrorHandler.checkElement(recentList, "recentList")) return;
        recentList.innerHTML = "<p class=\"loading-message\">Carregando buscas recentes...</p>";
        
        // Fazer requisição para a API
        const response = await fetch("/api/recent");
        
        if (!response.ok) {
            throw new Error("Erro ao carregar buscas recentes");
        }
        
        const data = await response.json();
        
        // Limpar lista novamente
        recentList.innerHTML = "";
        
        if (data.length === 0) {
            recentList.innerHTML = "<p class=\"loading-message\">Nenhuma busca recente encontrada.</p>";
            return;
        }
        
        // Adicionar cada item à lista
        data.forEach(item => {
            if (!recentSearchItemTemplate) {
                console.error("Template recent-search-item-template não encontrado!");
                return;
            }
            const recentItemElement = recentSearchItemTemplate.content.cloneNode(true);
            
            const queryElement = recentItemElement.querySelector(".recent-query");
            const timeElement = recentItemElement.querySelector(".recent-time");
            const viewButton = recentItemElement.querySelector(".btn-view");
            
            // Usa UIErrorHandler para definir o conteúdo e adicionar evento com segurança
            UIErrorHandler.setTextContent(queryElement, item.query, ".recent-query");
            UIErrorHandler.setTextContent(timeElement, item.timestamp, ".recent-time");
            UIErrorHandler.addEventListener(viewButton, "click", () => loadPreviousSearch(item.file), ".btn-view");
            
            recentList.appendChild(recentItemElement);
        });
        
    } catch (error) {
        errorHandler.logError("Main", "loadRecentSearches", error);
        if (UIErrorHandler.checkElement(recentList, "recentList")) {
            recentList.innerHTML = `<p class="loading-message error">Erro ao carregar buscas recentes: ${error.message}</p>`;
        }
        console.error("Erro ao carregar buscas recentes:", error);
    }
}

// Função para carregar uma busca anterior
async function loadPreviousSearch(filename) {
    try {
        // Mostrar status de carregamento
        showStatus("<div class=\"spinner\"></div> Carregando resultados...", "loading");
        
        // Fazer requisição para a API
        const response = await fetch(`/api/results/${filename}`);
        
        if (!response.ok) {
            throw new Error("Erro ao carregar resultados");
        }
        
        const data = await response.json();
        
        // Salvar resultados atuais
        currentResults = data;
        
        // Exibir resultados
        displayResults(data);
        
        // Atualizar campo de busca
        if (UIErrorHandler.checkElement(searchInput, "searchInput")) {
            searchInput.value = data.query;
        }
        
        // Limpar status
        showStatus("");
        
    } catch (error) {
        errorHandler.logError("Main", "loadPreviousSearch", error);
        showStatus(`Erro: ${error.message}`, "error");
        console.error("Erro ao carregar busca anterior:", error);
    }
}

// Função para exibir mensagens de status
function showStatus(message, type = "") {
    if (!UIErrorHandler.checkElement(searchStatus, "searchStatus")) return;
    searchStatus.innerHTML = message;
    searchStatus.className = "search-status"; // Reseta classes
    
    if (type) {
        searchStatus.classList.add(type);
    }
}
