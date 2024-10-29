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
from flask_cors import CORS
import io
import base64
import json
import gmaps

# Configurações para NLTK
nltk.download('punkt')
nltk.download('stopwords')

# Inicializar o Flask
app = Flask(__name__, template_folder='.')
CORS(app, origins=["https://rqpaiva.github.io"])

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

# Função para criação e exibição de tabelas
def create_and_display_tables(df):
    general_info = pd.DataFrame({
        'Description': ['Total Rows', 'Total Columns', 'Categorical Variables', 'Variables with Missing Data'],
        'Value': [df.shape[0], df.shape[1], df.select_dtypes(include=['object', 'category']).shape[1], df.isnull().sum().gt(0).sum()]
    })
    
    missing_data = df.isnull().sum().reset_index()
    missing_data.columns = ['Variable', 'Missing Count']
    missing_data = missing_data[missing_data['Missing Count'] > 0]
    
    return general_info, missing_data

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
    
    return pd.DataFrame(summary_data, columns=['Característica', 'Classe', 'Contagem', 'Percentual', 'Pontuação Média'])

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
    
    return summary_data

# Função para criar e exibir tabela de informações espaciais
def create_spatial_info_table(df):
    summary_data = []
    for char in ['zona_driver', 'zona_client']:
        for status in df['status'].unique():
            counts = df[df['status'] == status][char].value_counts()
            total = counts.sum()
            for value, count in counts.items():
                summary_data.append([char, value, status, count, f"{count / total:.2%}"])
    
    return pd.DataFrame(summary_data, columns=['Característica', 'Classe', 'Status das Corridas', 'Contagem', 'Percentual'])

# Função para análise de comentários com rede de relacionamento
def analyze_comments(df):
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

    sentiment_distribution = df_comments['sentiment'].value_counts().reset_index()
    sentiment_distribution.columns = ['Sentiment', 'Count']
    
    return sentiment_distribution

# Rota para carregar e processar o arquivo CSV
@app.route('/upload', methods=['POST'])
def upload_file():
    global df
    file = request.files['file']
    if not file:
        return jsonify({"error": "Nenhum arquivo foi enviado!"}), 400

    # Carregar o arquivo CSV em um DataFrame
    df = pd.read_csv(file)
    df = apply_mappings(df)

    # Calcular tabelas e estatísticas iniciais
    general_info, missing_data = create_and_display_tables(df)
    personal_info_table = create_personal_info_table(df)
    temporal_analysis = create_temporal_analysis(df)
    spatial_info_table = create_spatial_info_table(df)
    comment_analysis = analyze_comments(df)

    # Serializar dados para JSON
    response_data = {
        "general_info": general_info.to_dict(orient='records'),
        "missing_data": missing_data.to_dict(orient='records'),
        "personal_info_table": personal_info_table.to_dict(orient='records'),
        "temporal_analysis": [t.to_dict(orient='records') for t in temporal_analysis],
        "spatial_info_table": spatial_info_table.to_dict(orient='records'),
        "comment_analysis": comment_analysis.to_dict(orient='records')
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
