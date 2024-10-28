# Importar bibliotecas
from flask import Flask, request, jsonify, render_template
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import networkx as nx
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from tabulate import tabulate
import io
import base64
import json

# Configurações para NLTK
nltk.download('punkt')
nltk.download('stopwords')

# Inicializar o Flask
app = Flask(__name__)

# Variável global para armazenar os dados carregados
df = None

# Funções de análise (mantenha todas as funções de análise definidas aqui, como no código original)

# Mapear variáveis categóricas e zonas
def apply_mappings(df):
    mappings = {
        'gender': {2: 'Feminino', 1: 'Masculino'},
        'race': {-1: 'Asiatico', 0: 'Branco', 1: 'Pardo', 2: 'Negro'},
        'age_Range': {0: 'Jovem (abaixo de 30)', 1: 'Adulto (30 a 60)', 2: 'Senior (acima de 60)'},
        'fitness': {-1: 'Magro', 0: 'Normal', 1: 'Gordo'}
    }
    for col, mapping in mappings.items():
        df[col] = df[col].map(mapping)
    return df

# Rota para carregar e processar o arquivo CSV
@app.route('/upload', methods=['POST'])
def upload_file():
    global df
    file = request.files['file']
    if not file:
        return jsonify({"error": "Nenhum arquivo foi enviado!"}), 400

    df = pd.read_csv(file)
    df = apply_mappings(df)

    # Calcular tabelas e estatísticas iniciais
    general_info, missing_data = create_and_display_tables(df)
    personal_info_table = create_personal_info_table(df)

    # Serializar dados para JSON
    response_data = {
        "general_info": general_info.to_dict(orient='records'),
        "missing_data": missing_data.to_dict(orient='records'),
        "personal_info_table": personal_info_table.to_dict(orient='records')
    }

    return jsonify(response_data)

# Rota para aplicar filtros e retornar resultados de análise
@app.route('/analyze', methods=['POST'])
def analyze():
    global df
    if df is None:
        return jsonify({"error": "Nenhum arquivo foi carregado!"}), 400

    # Obter filtros do frontend
    data = request.get_json()
    gender = data.get("gender")
    age_range = data.get("ageRange")
    radius = data.get("radius")
    
    # Aplicar filtros no DataFrame `df`
    filtered_df = df.copy()
    if gender:
        filtered_df = filtered_df[filtered_df['gender'] == gender]
    if age_range:
        filtered_df = filtered_df[filtered_df['age_Range'] == age_range]
    # Adicione outros filtros aqui, conforme necessário

    # Realizar análise e gerar estatísticas
    statistics_html = filtered_df.describe().to_html()  # Exemplo de estatísticas
    heatmap_html = "<div>Aqui será exibido o mapa de calor.</div>"  # Placeholder para o mapa de calor

    return jsonify({
        "statisticsHtml": statistics_html,
        "heatmapHtml": heatmap_html
    })

# Rota principal para exibir a interface
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)


# Mapear variáveis categóricas e zonas
def apply_mappings(df):
    mappings = {
        'gender': {2: 'Feminino', 1: 'Masculino'},
        'race': {-1: 'Asiatico', 0: 'Branco', 1: 'Pardo', 2: 'Negro'},
        'age_Range': {0: 'Jovem (abaixo de 30)', 1: 'Adulto (30 a 60)', 2: 'Senior (acima de 60)'},
        'fitness': {-1: 'Magro', 0: 'Normal', 1: 'Gordo'}
    }
    for col, mapping in mappings.items():
        df[col] = df[col].map(mapping)
    return df

df = apply_mappings(df)

# Função para criação e exibição de tabelas
def create_and_display_tables(df):
    general_info = pd.DataFrame({
        'Description': ['Total Rows', 'Total Columns', 'Categorical Variables', 'Variables with Missing Data'],
        'Value': [df.shape[0], df.shape[1], df.select_dtypes(include=['object', 'category']).shape[1], df.isnull().sum().gt(0).sum()]
    })
    
    missing_data = df.isnull().sum().reset_index()
    missing_data.columns = ['Variable', 'Missing Count']
    missing_data = missing_data[missing_data['Missing Count'] > 0]
    
    print("Informações gerais da base de dados:")
    print(tabulate(general_info, headers='keys', tablefmt='grid', showindex=False))
    print("\nDados faltantes na base:")
    print(tabulate(missing_data, headers='keys', tablefmt='grid', showindex=False))

create_and_display_tables(df)

# Função para exibir distribuição de dados por características pessoais, incluindo a média das avaliações dos motoristas
def create_personal_info_table(df):
    summary_data = []
    personal_info = ['gender', 'race', 'age_Range', 'fitness']
    
    # Calcular média da pontuação dos motoristas
    driver_ratings = df.groupby('driver_id')['rating_score'].mean().reset_index()
    driver_ratings.columns = ['driver_id', 'Pontuação Média do Motorista']
    df = df.merge(driver_ratings, on='driver_id', how='left')
    
    for char in personal_info:
        char_counts = df[char].value_counts(dropna=False)
        total = char_counts.sum()
        for value, count in char_counts.items():
            avg_score = df[df[char] == value]['Pontuação Média do Motorista'].mean()
            summary_data.append([char, value, count, f"{count / total:.2%}", f"{avg_score:.2f}"])
    
    table2 = pd.DataFrame(summary_data, columns=['Característica', 'Classe', 'Contagem', 'Percentual', 'Pontuação Média'])
    print("Informações Pessoais com Pontuação Média:")
    print(tabulate(table2, headers='keys', tablefmt='grid', showindex=False))

create_personal_info_table(df)

# Função para análise e exibição de estatísticas temporais
def create_temporal_analysis(df):
    temporal_info = ['turno', 'hour', 'week_day', 'day_group', 'time_estimate', 'duration', 'duration_trip']
    summary_data = []
    
    for char in temporal_info:
        if char in ['hour', 'time_estimate', 'duration', 'duration_trip']:
            mean_by_status = df.groupby('status')[char].mean().reset_index()
            mean_by_status.columns = ['Status', f'Média {char}']
            summary_data.append(mean_by_status)
        else:
            count_by_status = df.groupby(['status', char]).size().reset_index(name='Count')
            summary_data.append(count_by_status)
    
    for data in summary_data:
        print(tabulate(data, headers='keys', tablefmt='grid', showindex=False))

create_temporal_analysis(df)

# Função para mapeamento de zonas
zona_norte = ['Abolição', 'Acari', 'Água Santa', 'Alto da Boa Vista', 'Anchieta', 'Andaraí', 'Bancários', 'Barros Filho', 'Bento Ribeiro', 'Bonsucesso', 'Brás de Pina', 'Cachambi', 'Cacuia', 'Campinho', 'Cascadura', 'Cavalcanti', 'Cidade Universitária', 'Cocotá', 'Coelho Neto', 'Colégio', 'Complexo do Alemão', 'Cordovil', 'Costa Barros', 'Del Castilho', 'Encantado', 'Engenheiro Leal', 'Engenho da Rainha', 'Engenho de Dentro', 'Engenho Novo', 'Freguesia (Ilha do Governador)', 'Galeão', 'Guadalude', 'Grajaú', 'Higienópolis', 'Honório Gurgel', 'Inhaúma', 'Irajá', 'Jacaré', 'Jacarezinho', 'Jardim América', 'Jardim Carioca', 'Jardim Guanabara', 'Lins de Vasconcelos', 'Madureira', 'Manguinhos', 'Maracanã', 'Maré', 'Marechal Hermes', 'Maria da Graça', 'Méier', 'Moneró', 'Olaria', 'Oswaldo Cruz', 'Osvaldo Cruz', 'Parada de Lucas', 'Parque Anchieta', 'Parque Colúmbia', 'Pavuna', 'Penha', 'Penha Circular', 'Piedade', 'Pilares', 'Pitangueiras', 'Portuguesa', 'Praça da Bandeira', 'Praia da Bandeira', 'Quintino Bocaiúva', 'Ramos', 'Riachuelo', 'Rocha', 'Rocha Miranda', 'Sampaio', 'São Francisco Xavier', 'Tijuca', 'Todos os Santos', 'Tomás Coelho', 'Turiaçu', 'Vaz Lobo', 'Vicente de Carvalho', 'Vila da Penha', 'Vila Kosmos', 'Vigário Geral', 'Vista Alegre', 'Vila Isabel']
zona_sul = ['Botafogo', 'Catete', 'Copacabana', 'Cosme Velho', 'Flamengo', 'Gávea', 'Humaitá', 'Ipanema', 'Jardim Botânico', 'Lagoa', 'Laranjeiras', 'Leblon', 'Leme', 'Rocinha', 'São Conrado', 'Urca', 'Vidigal']
zona_oeste = ['Anil', 'Bangu', 'Barra da Tijuca', 'Barra de Guaratiba', 'Barra Olímpica', 'Camorim', 'Campo dos Afonsos', 'Campo Grande', 'Cidade de Deus', 'Cosmos', 'Curicica', 'Deodoro', 'Freguesia (Jacarepaguá)', 'Gardênia Azul', 'Gericinó', 'Grumari', 'Guaratiba', 'Inhoaíba', 'Itanhangá', 'Jacarepaguá', 'Jardim Sulacap', 'Joá', 'Magalhães Bastos', 'Paciência', 'Padre Miguel', 'Pechincha', 'Pedra de Guaratiba', 'Praça Seca', 'Realengo', 'Recreio dos Bandeirantes', 'Santa Cruz', 'Santíssimo', 'Senador Camará', 'Senador Vasconcelos', 'Sepetiba', 'Tanque', 'Taquara', 'Vargem Grande', 'Vargem Pequena', 'Vila Kennedy', 'Vila Militar', 'Vila Valqueire']
zona_central = ['Benfica', 'Caju', 'Catumbi', 'Centro', 'Cidade Nova', 'Estácio', 'Gamboa', 'Glória', 'Lapa', 'Mangueira', 'Paquetá', 'Rio Comprido', 'Santa Teresa', 'Santo Cristo', 'Santos Dumont', 'São Cristóvão', 'Saúde', 'Vasco da Gama']

def mapear_zona(bairro):
    if bairro in zona_norte:
        return 'Zona Norte'
    elif bairro in zona_sul:
        return 'Zona Sul'
    elif bairro in zona_oeste:
        return 'Zona Oeste'
    elif bairro in zona_central:
        return 'Zona Central'
    else:
        return 'Outros'

df['zona_driver'] = df['suburb_driver'].apply(mapear_zona)
df['zona_client'] = df['suburb_client'].apply(mapear_zona)

# Função para criar e exibir tabela de informações espaciais
def create_spatial_info_table(df):
    summary_data = []
    for char in ['zona_driver', 'zona_client']:
        for status in df['status'].unique():
            counts = df[df['status'] == status][char].value_counts()
            total = counts.sum()
            for value, count in counts.items():
                summary_data.append([char, value, status, count, f"{count / total:.2%}"])
    
    table4 = pd.DataFrame(summary_data, columns=['Característica', 'Classe', 'Status das Corridas', 'Contagem', 'Percentual'])
    print("Informações Espaciais:")
    print(tabulate(table4, headers='keys', tablefmt='grid', showindex=False))

create_spatial_info_table(df)

# Função para plotar o mapa de calor das corridas canceladas
def plot_heatmap(df, lat_col, lng_col, title):
    locations = df[[lat_col, lng_col]].dropna()
    fig = gmaps.figure(center=(locations[lat_col].mean(), locations[lng_col].mean()), zoom_level=12)
    heatmap_layer = gmaps.heatmap_layer(locations)
    fig.add_layer(heatmap_layer)
    return fig

heatmap_fig_taxista = plot_heatmap(df[df['status'] == 'cancelada pelo taxista'], 'origin_lat', 'origin_lng', 'Canceladas pelo Taxista')
heatmap_fig_passageiro = plot_heatmap(df[df['status'] == 'cancelada pelo passageiro'], 'origin_lat', 'origin_lng', 'Canceladas pelo Passageiro')

# Análise de Comentários com Rede de Relacionamento
df['status'] = df['status'].str.strip().str.lower()
df['rating_comment'] = df['rating_comment'].astype(str).str.strip().str.lower()

df_comments = df[(df['status'] == 'finalizada') & df['rating_comment'].notna() & (df['rating_comment'] != 'comentarios opcional')]

def analyze_sentiment(score):
    if score >= 4:
        return 'positive'
    elif score <= 2:
        return 'negative'
    else:
        return 'neutral'

df_comments['sentiment'] = df_comments['rating_score'].apply(analyze_sentiment)

car_keywords = ['confortável', 'limpo', 'rápido', 'espaçoso', 'silencioso', 'desconfortável', 'sujo', 'lento', 
                'carro', 'veículo', 'cheiro', 'odor', 'cigarro', 'quente', 'ar-condicionado']

df_comments['mentions_car_aspects'] = df_comments['rating_comment'].apply(lambda x: any(keyword in x for keyword in car_keywords))
aspect_comments = df_comments[df_comments['mentions_car_aspects']]

positive_comments = aspect_comments[aspect_comments['sentiment'] == 'positive']
neutral_comments = aspect_comments[aspect_comments['sentiment'] == 'neutral']
negative_comments = aspect_comments[aspect_comments['sentiment'] == 'negative']

stop_words = set(stopwords.words('portuguese'))

def preprocess_text(text):
    tokens = word_tokenize(text)
    return [word for word in tokens if word.isalpha() and word not in stop_words]

def plot_word_relationship(comments, title, top_n=20):
    comments['tokens'] = comments['rating_comment'].apply(preprocess_text)
    all_words = [word for tokens in comments['tokens'] for word in tokens]
    word_freq = Counter(all_words)
    most_common_words = [word for word, freq in word_freq.most_common(top_n)]

    G = nx.Graph()
    for word, freq in word_freq.items():
        if word in most_common_words:
            G.add_node(word, size=freq)

    for tokens in comments['tokens']:
        for i, word1 in enumerate(tokens):
            if word1 in most_common_words:
                for word2 in tokens[i+1:]:
                    if word2 in most_common_words:
                        if G.has_edge(word1, word2):
                            G[word1][word2]['weight'] += 1
                        else:
                            G.add_edge(word1, word2, weight=1)

    plt.figure(figsize=(14, 14))
    pos = nx.spring_layout(G, k=0.3)
    sizes = [G.nodes[node]['size'] * 50 for node in G.nodes]
    nx.draw_networkx_nodes(G, pos, node_size=sizes, alpha=0.6)
    nx.draw_networkx_edges(G, pos, width=0.2, alpha=0.5)
    nx.draw_networkx_labels(G, pos, font_size=12)
    plt.title(title)
    plt.show()

plot_word_relationship(positive_comments, 'Rede de Relacionamento - Comentários Positivos')
plot_word_relationship(neutral_comments, 'Rede de Relacionamento - Comentários Neutros')
plot_word_relationship(negative_comments, 'Rede de Relacionamento - Comentários Negativos')

# Distribuição de Sentimentos nos Comentários
sentiment_distribution = df_comments['sentiment'].value_counts().reset_index()
sentiment_distribution.columns = ['Sentiment', 'Count']
print("Distribuição de Sentimentos nos Comentários:")
print(tabulate(sentiment_distribution, headers='keys', tablefmt='grid', showindex=False))