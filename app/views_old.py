from app import app
import pandas as pd
from flask import render_template, request

ALLOWED_EXTENSIONS = {'csv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def home():
    data_html = None  
    if request.method == 'POST':
        
        if 'file' not in request.files:
            return 'Nenhum arquivo foi enviado.'
        file = request.files['file']

        if file.filename == '':
            return 'Nenhum arquivo selecionado.'

        if file and allowed_file(file.filename):
            try:
                
                data = pd.read_csv(file)

                
                if 'status' not in data.columns or 'Address_client_dict' not in data.columns:
                    return 'As colunas necessárias não estão presentes no arquivo.'

                
                def extract_address_info(address):
                    try:
                        address_dict = eval(address) 
                        return pd.Series({
                            'road': address_dict.get('road'),
                            'suburb': address_dict.get('suburb'),
                            'state': address_dict.get('state')
                        })
                    except Exception as e:
                        return pd.Series({'road': None, 'suburb': None, 'state': None})

               
                address_info = data['Address_client_dict'].apply(extract_address_info)
                filtered_data = pd.concat([data[['status']], address_info], axis=1)

               
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




