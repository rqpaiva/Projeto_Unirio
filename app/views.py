from app import app
import pandas as pd
from flask import render_template, request, jsonify

ALLOWED_EXTENSIONS = {'csv'}
df = None  # Variável global para armazenar dados carregados

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Função para extrair informações de endereço
def extract_address_info(address):
    try:
        address_dict = eval(address)  # Avalia a string como um dicionário
        return pd.Series({
            'road': address_dict.get('road'),
            'suburb': address_dict.get('suburb'),
            'state': address_dict.get('state')
        })
    except Exception:
        return pd.Series({'road': None, 'suburb': None, 'state': None})

# Funções de Mapeamento e Análise
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
    
# Rota principal
@app.route('/', methods=['GET', 'POST'])
def home():
    global df
    data_html = None

    if request.method == 'POST':
        if 'file' not in request.files:
            return 'Nenhum arquivo foi enviado.'
        
        file = request.files['file']
        if file.filename == '':
            return 'Nenhum arquivo selecionado.'

        if file and allowed_file(file.filename):
            try:
                df = pd.read_csv(file)
                df = apply_mappings(df)  # Aplicar mapeamento

                # Filtrar e extrair colunas
                address_info = df['Address_client_dict'].apply(extract_address_info)
                filtered_data = pd.concat([df[['status']], address_info], axis=1)

                filtered_data.rename(columns={
                    'road': 'Rua',
                    'suburb': 'Bairro',
                    'state': 'Estado',
                    'status': 'Status'
                }, inplace=True)

                data_html = filtered_data.to_html(classes='table table-striped', index=False)

            except Exception as e:
                return f'Ocorreu um erro ao processar o arquivo: {e}'

    return render_template('index.html', data=data_html)

# Rota para exibir novas análises
@app.route('/analyze', methods=['POST'])
def analyze():
    global df
    if df is None:
        return jsonify({"error": "Nenhum arquivo foi carregado!"}), 400

    # Análises estatísticas adicionais
    general_info, missing_data = create_and_display_tables(df)
    # Aqui você pode adicionar outras análises, por exemplo, `create_personal_info_table(df)`
    personal_info_table = create_personal_info_table(df)
    temporal_analysis = create_temporal_analysis(df)
    spatial_info_table = create_spatial_info_table(df)
    comment_analysis = analyze_comments(df)


    response_data = {
        "general_info": general_info.to_dict(orient='records'),
        "missing_data": missing_data.to_dict(orient='records'),
        # Adicione outras tabelas de análise conforme desejado
        
    }
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)