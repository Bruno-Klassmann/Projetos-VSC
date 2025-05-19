/**
 * Testes para o módulo de formatação de números
 * 
 * Este script testa a funcionalidade de parsing e formatação de números
 * com diferentes formatos de entrada para garantir que a conversão
 * funcione corretamente em todos os cenários.
 */

// Função para executar os testes
function runNumberFormattingTests() {
    console.log('Iniciando testes de formatação de números...');
    
    // Cria uma instância do formatador de números
    const formatter = new NumberFormatter('pt-BR');
    formatter.setDebug(true);
    
    // Array de casos de teste para parsing de preços
    const parsePriceTests = [
        { input: 'R$ 1.234,56', expected: 1234.56, description: 'Formato brasileiro com símbolo de moeda' },
        { input: '1.234,56', expected: 1234.56, description: 'Formato brasileiro sem símbolo de moeda' },
        { input: '1234,56', expected: 1234.56, description: 'Formato europeu' },
        { input: 'R$ 1,234.56', expected: 1234.56, description: 'Formato americano com símbolo de moeda' },
        { input: '1,234.56', expected: 1234.56, description: 'Formato americano sem símbolo de moeda' },
        { input: '1234.56', expected: 1234.56, description: 'Formato americano sem separador de milhar' },
        { input: '1234', expected: 1234, description: 'Número inteiro sem separadores' },
        { input: 'R$ 1.234', expected: 1234, description: 'Número inteiro com separador de milhar brasileiro' },
        { input: 'R$ 1,234', expected: 1234, description: 'Número inteiro com separador de milhar americano' },
        { input: 'R$ 0,99', expected: 0.99, description: 'Valor menor que 1 em formato brasileiro' },
        { input: 'R$ 0.99', expected: 0.99, description: 'Valor menor que 1 em formato americano' },
        { input: 'R$ 1.234.567,89', expected: 1234567.89, description: 'Valor grande em formato brasileiro' },
        { input: 'R$ 1,234,567.89', expected: 1234567.89, description: 'Valor grande em formato americano' },
        { input: 'Preço: R$ 1.234,56', expected: 1234.56, description: 'Texto antes do preço' },
        { input: 'R$ 1.234,56 à vista', expected: 1234.56, description: 'Texto depois do preço' },
        { input: '', expected: null, description: 'String vazia' },
        { input: 'Indisponível', expected: null, description: 'Texto sem números' },
        { input: null, expected: null, description: 'Valor null' },
        { input: undefined, expected: null, description: 'Valor undefined' }
    ];
    
    // Executa os testes de parsing de preços
    console.log('\n=== TESTES DE PARSING DE PREÇOS ===');
    let passedParseTests = 0;
    
    parsePriceTests.forEach((test, index) => {
        try {
            const result = formatter.parsePrice(test.input);
            const passed = result === test.expected || 
                          (result === null && test.expected === null) ||
                          (result !== null && test.expected !== null && Math.abs(result - test.expected) < 0.001);
            
            console.log(`Teste ${index + 1}: ${passed ? 'PASSOU ✓' : 'FALHOU ✗'}`);
            console.log(`  Descrição: ${test.description}`);
            console.log(`  Entrada: ${JSON.stringify(test.input)}`);
            console.log(`  Resultado: ${result}`);
            console.log(`  Esperado: ${test.expected}`);
            
            if (passed) {
                passedParseTests++;
            }
        } catch (error) {
            console.log(`Teste ${index + 1}: ERRO ✗`);
            console.log(`  Descrição: ${test.description}`);
            console.log(`  Entrada: ${JSON.stringify(test.input)}`);
            console.log(`  Erro: ${error.message}`);
        }
    });
    
    // Array de casos de teste para formatação de moeda
    const formatCurrencyTests = [
        { input: 1234.56, expected: 'R$ 1.234,56', description: 'Valor decimal positivo' },
        { input: 1234, expected: 'R$ 1.234,00', description: 'Valor inteiro positivo' },
        { input: 0.99, expected: 'R$ 0,99', description: 'Valor menor que 1' },
        { input: 1234567.89, expected: 'R$ 1.234.567,89', description: 'Valor grande' },
        { input: 0, expected: 'R$ 0,00', description: 'Zero' },
        { input: -1234.56, expected: '-R$ 1.234,56', description: 'Valor negativo' },
        { input: null, expected: 'Preço indisponível', description: 'Valor null' },
        { input: undefined, expected: 'Preço indisponível', description: 'Valor undefined' },
        { input: NaN, expected: 'Preço indisponível', description: 'Valor NaN' }
    ];
    
    // Executa os testes de formatação de moeda
    console.log('\n=== TESTES DE FORMATAÇÃO DE MOEDA ===');
    let passedFormatTests = 0;
    
    formatCurrencyTests.forEach((test, index) => {
        try {
            const result = formatter.formatCurrency(test.input);
            // Nota: A formatação exata pode variar dependendo do navegador e da localização,
            // então verificamos se o resultado contém os elementos esperados
            const passed = result === test.expected || 
                          (result.includes('indisponível') && test.expected.includes('indisponível'));
            
            console.log(`Teste ${index + 1}: ${passed ? 'PASSOU ✓' : 'FALHOU ✗'}`);
            console.log(`  Descrição: ${test.description}`);
            console.log(`  Entrada: ${test.input}`);
            console.log(`  Resultado: ${result}`);
            console.log(`  Esperado: ${test.expected}`);
            
            if (passed) {
                passedFormatTests++;
            }
        } catch (error) {
            console.log(`Teste ${index + 1}: ERRO ✗`);
            console.log(`  Descrição: ${test.description}`);
            console.log(`  Entrada: ${test.input}`);
            console.log(`  Erro: ${error.message}`);
        }
    });
    
    // Testes de integração: parsing seguido de formatação
    console.log('\n=== TESTES DE INTEGRAÇÃO ===');
    const integrationTests = [
        { input: 'R$ 1.234,56', description: 'Formato brasileiro' },
        { input: '1,234.56', description: 'Formato americano' },
        { input: '1234,56', description: 'Formato europeu' }
    ];
    
    let passedIntegrationTests = 0;
    
    integrationTests.forEach((test, index) => {
        try {
            const parsedValue = formatter.parsePrice(test.input);
            const formattedValue = formatter.formatCurrency(parsedValue);
            
            console.log(`Teste ${index + 1}:`);
            console.log(`  Descrição: ${test.description}`);
            console.log(`  Entrada: ${test.input}`);
            console.log(`  Valor parseado: ${parsedValue}`);
            console.log(`  Valor formatado: ${formattedValue}`);
            
            // Verifica se o valor parseado não é null
            if (parsedValue !== null) {
                passedIntegrationTests++;
                console.log(`  Resultado: PASSOU ✓`);
            } else {
                console.log(`  Resultado: FALHOU ✗ (valor parseado é null)`);
            }
        } catch (error) {
            console.log(`Teste ${index + 1}: ERRO ✗`);
            console.log(`  Descrição: ${test.description}`);
            console.log(`  Entrada: ${test.input}`);
            console.log(`  Erro: ${error.message}`);
        }
    });
    
    // Resumo dos resultados
    console.log('\n=== RESUMO DOS TESTES ===');
    console.log(`Testes de parsing: ${passedParseTests}/${parsePriceTests.length} passaram`);
    console.log(`Testes de formatação: ${passedFormatTests}/${formatCurrencyTests.length} passaram`);
    console.log(`Testes de integração: ${passedIntegrationTests}/${integrationTests.length} passaram`);
    console.log(`Total: ${passedParseTests + passedFormatTests + passedIntegrationTests}/${parsePriceTests.length + formatCurrencyTests.length + integrationTests.length} passaram`);
    
    return {
        parseTests: { passed: passedParseTests, total: parsePriceTests.length },
        formatTests: { passed: passedFormatTests, total: formatCurrencyTests.length },
        integrationTests: { passed: passedIntegrationTests, total: integrationTests.length },
        total: { 
            passed: passedParseTests + passedFormatTests + passedIntegrationTests, 
            total: parsePriceTests.length + formatCurrencyTests.length + integrationTests.length 
        }
    };
}

// Executa os testes quando o script é carregado
document.addEventListener('DOMContentLoaded', () => {
    // Verifica se estamos em modo de teste
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('test') && urlParams.get('test') === 'number-formatting') {
        console.log('Modo de teste ativado');
        const results = runNumberFormattingTests();
        
        // Exibe os resultados na página
        const testResultsElement = document.createElement('div');
        testResultsElement.className = 'test-results';
        testResultsElement.innerHTML = `
            <h2>Resultados dos Testes de Formatação de Números</h2>
            <p>Testes de parsing: ${results.parseTests.passed}/${results.parseTests.total} passaram</p>
            <p>Testes de formatação: ${results.formatTests.passed}/${results.formatTests.total} passaram</p>
            <p>Testes de integração: ${results.integrationTests.passed}/${results.integrationTests.total} passaram</p>
            <p><strong>Total: ${results.total.passed}/${results.total.total} passaram</strong></p>
            <p>Veja o console para detalhes dos testes.</p>
        `;
        
        // Adiciona os resultados à página
        document.body.prepend(testResultsElement);
    }
});
