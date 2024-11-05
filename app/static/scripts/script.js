document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const fileLabel = document.querySelector('.custom-file-label');
    const textUpload = document.querySelector('.text-upload');
    const buttonSubimit = document.querySelector('.buttonSubimit');
    const analyzeButton = document.getElementById('analyze-btn');

    // Desabilite o botão "Realizar Análise" até que o upload seja bem-sucedido
    analyzeButton.disabled = true;
    
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            textUpload.textContent = fileInput.files[0].name;
            fileLabel.classList.add('hidenButton');
            buttonSubimit.classList.remove('hidenButton')

        } else {
            fileLabel.textContent = 'Nenhum arquivo selecionado';
        }
    });

    // Habilite o botão "Realizar Análise" após o envio do formulário de upload
    $('#uploadForm').on('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        $.ajax({
            url: '/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                analyzeButton.disabled = false; // Habilita o botão "Realizar Análise"
                alert('Arquivo carregado com sucesso. Agora você pode realizar a análise.');
            },
            error: function(xhr, status, error) {
                alert(`Erro ao carregar o arquivo. Status: ${status}, Erro: ${error}`);
                console.error("Detalhes da resposta:", xhr.responseText);
            }
        });
    });

    // Ação do botão "Realizar Análise"
    $('#analyze-btn').on('click', function() {
        $.ajax({
            url: '/analyze',
            type: 'POST',
            success: function(response) {
                // Verifica e renderiza as tabelas apenas se contiverem dados
                if (response.general_info && response.general_info.length > 0) {
                    $('#general-info').html(createTable(response.general_info));
                }
                if (response.missing_data && response.missing_data.length > 0) {
                    $('#missing-data').html(createTable(response.missing_data));
                }
                if (response.personal_info_table && response.personal_info_table.length > 0) {
                    $('#personal-info').html(createTable(response.personal_info_table));
                }
                if (response.temporal_analysis) {
                    let temporalHtml = '';
                    for (const [key, data] of Object.entries(response.temporal_analysis)) {
                        if (data && data.length > 0) {  // Verifique se há dados antes de criar a tabela
                            temporalHtml += `<h4>${key}</h4>`;
                            temporalHtml += createTable(data);
                        }
                    }
                    $('#temporal-analysis').html(temporalHtml);
                }
                if (response.spatial_info_table && response.spatial_info_table.length > 0) {
                    $('#spatial-info').html(createTable(response.spatial_info_table));
                }
                if (response.comment_analysis && response.comment_analysis.length > 0) {
                    $('#comment-analysis').html(createTable(response.comment_analysis));
                }
            },
            error: function(xhr, status, error) {
                alert(`Erro ao realizar a análise. Status: ${status}, Erro: ${error}`);
                console.error("Detalhes da resposta:", xhr.responseText);
            }
        });
    });

    // Função para criar a tabela HTML a partir dos dados JSON
    function createTable(data) {
        if (!data || data.length === 0) return '<p>Nenhuma informação disponível.</p>'; // Retorna uma mensagem se não houver dados

        var table = '<table class="table table-striped">';
        table += '<thead><tr>';
        Object.keys(data[0]).forEach(function(key) {
            table += '<th>' + key + '</th>';
        });
        table += '</tr></thead><tbody>';

        data.forEach(function(row) {
            table += '<tr>';
            Object.values(row).forEach(function(value) {
                // Verifica se o valor é NaN ou indefinido, substituindo por um texto amigável
                table += '<td>' + (value !== undefined && !isNaN(value) ? value : 'N/A') + '</td>';
            });
            table += '</tr>';
        });

        table += '</tbody></table>';
        return table;
    }
});