// Manipular upload do arquivo
document.getElementById("uploadForm").onsubmit = async function(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById("fileInput").files[0];
    const formData = new FormData();
    formData.append("file", fileInput);

    // Enviar o arquivo para o backend
    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        if (response.ok) {
            // Exibir os filtros após o upload bem-sucedido
            document.getElementById("filters").style.display = "block";
            alert("Arquivo carregado com sucesso. Agora você pode aplicar filtros.");
        } else {
            alert("Erro ao carregar o arquivo.");
        }
    } catch (error) {
        console.error("Erro ao enviar o arquivo:", error);
        alert("Ocorreu um erro ao enviar o arquivo.");
    }
};

// Manipular a aplicação de filtros e solicitação de análises
document.getElementById("applyFilters").onclick = async function() {
    const gender = document.getElementById("genderFilter").value;
    const ageRange = document.getElementById("ageRangeFilter").value;
    const radius = document.getElementById("radiusFilter").value;

    const params = {
        gender,
        ageRange,
        radius
    };

    try {
        // Enviar filtros para o backend
        const response = await fetch("/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(params)
        });

        if (response.ok) {
            const result = await response.json();
            displayResults(result);
        } else {
            alert("Erro ao aplicar filtros.");
        }
    } catch (error) {
        console.error("Erro ao aplicar filtros:", error);
        alert("Ocorreu um erro ao aplicar os filtros.");
    }
};

// Função para exibir os resultados da análise
function displayResults(result) {
    document.getElementById("statistics").innerHTML = result.statisticsHtml || "Nenhum dado de estatísticas disponível.";
    document.getElementById("heatmap").innerHTML = result.heatmapHtml || "Nenhum mapa de calor disponível.";
}