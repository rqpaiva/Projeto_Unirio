document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const fileLabel = document.querySelector('.custom-file-label');
    const textUpload = document.querySelector('.text-upload');
    const buttonSubimit = document.querySelector('.buttonSubimit');

    
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            textUpload.textContent = fileInput.files[0].name;
            fileLabel.classList.add('hidenButton');
            buttonSubimit.classList.remove('hidenButton')

        } else {
            fileLabel.textContent = 'Nenhum arquivo selecionado';
        }
    });
});

// Função para realizar a análise e exibir as novas tabelas
$('#analyze-btn').on('click', function() {
    $.ajax({
        url: '/analyze',
        type: 'POST',
        success: function(response) {
            if (response.general_info) {
                $('#general-info').html(createTable(response.general_info));
            }
            if (response.missing_data) {
                $('#missing-data').html(createTable(response.missing_data));
            }
            if (response.personal_info_table) {
                $('#personal-info').html(createTable(response.personal_info_table));
            }
            if (response.temporal_analysis) {
                let temporalHtml = '';
                for (const [key, data] of Object.entries(response.temporal_analysis)) {
                    temporalHtml += `<h4>${key}</h4>`;
                    temporalHtml += createTable(data);
                }
                $('#temporal-analysis').html(temporalHtml);
            }
            if (response.spatial_info_table) {
                $('#spatial-info').html(createTable(response.spatial_info_table));
            }
            if (response.comment_analysis) {
                $('#comment-analysis').html(createTable(response.comment_analysis));
            }
        },
        error: function(xhr, status, error) {
            alert(`Erro ao realizar a análise. Status: ${status}, Erro: ${error}`);
            console.error("Detalhes da resposta:", xhr.responseText);
        }
    });
});





