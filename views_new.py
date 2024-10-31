from app import app
import pandas as pd
from flask import render_template, request, jsonify

ALLOWED_EXTENSIONS = {'csv'}
df = None  # Variável global para armazenar dados carregados

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

    response_data = {
        "general_info": general_info.to_dict(orient='records'),
        "missing_data": missing_data.to_dict(orient='records'),
        # Adicione outras tabelas de análise conforme desejado
    }
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)
