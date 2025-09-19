from flask import Flask, render_template, request, jsonify
from flask_migrate import Migrate
from db import db
from models.convenios import Convenios, ConvenioStatus
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/termos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads') 
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf'}

db.init_app(app)
migrate = Migrate(app, db)

# Função auxiliar para verificar a extensão do arquivo
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Nova rota para servir o formulário HTML
@app.route('/')
def index():
    return render_template('index.html')

# Cadastrar Convênio
@app.route('/convenio', methods=['POST'])
def adicionar_convenio():
    try:
        # Obtém os dados de texto do formulário (request.form)
        nome_conveniada = request.form.get('nome_conveniada')
        cnpj = request.form.get('cnpj')
        nome_fantasia = request.form.get('nome_fantasia')
        cidade = request.form.get('cidade')
        estado = request.form.get('estado')
        area_atuacao = request.form.get('area_atuacao')
        qtd_funcionarios = request.form.get('qtd_funcionarios', type=int)
        qtd_associados = request.form.get('qtd_associados', type=int)
        qtd_sindicalizados = request.form.get('qtd_sindicalizados', type=int)
        responsavel_legal = request.form.get('responsavel_legal')
        cargo_responsavel = request.form.get('cargo_responsavel')
        email_responsavel = request.form.get('email_responsavel')
        telefone_responsavel = request.form.get('telefone_responsavel')
        unidade_uniesp = request.form.get('unidade_uniesp')
        diretor_responsavel = request.form.get('diretor_responsavel')
        data_assinatura_str = request.form.get('data_assinatura')
        observacoes = request.form.get('observacoes')
        status_str = request.form.get('status')
        
        # Converte a string de data para um objeto datetime.date
        data_assinatura = datetime.strptime(data_assinatura_str, '%Y-%m-%d').date() if data_assinatura_str else None
        
        # Converte a string de status para o Enum
        status = ConvenioStatus(status_str) if status_str in [e.value for e in ConvenioStatus] else None
        
        # Prepara o arquivo, mas NÃO o salva ainda
        arquivo = request.files.get('caminho_arquivo_pdf')
        caminho_arquivo = None
        if arquivo and allowed_file(arquivo.filename):
            nome_seguro = secure_filename(arquivo.filename)
            nome_arquivo_unico = str(uuid.uuid4()) + "_" + nome_seguro
            caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo_unico)

        # Cria o novo objeto Convenios com todos os dados
        novoConvenio = Convenios(
            nome_conveniada=nome_conveniada,
            cnpj=cnpj,
            nome_fantasia=nome_fantasia,
            cidade=cidade,
            estado=estado,
            area_atuacao=area_atuacao,
            qtd_funcionarios=qtd_funcionarios,
            qtd_associados=qtd_associados,
            qtd_sindicalizados=qtd_sindicalizados,
            responsavel_legal=responsavel_legal,
            cargo_responsavel=cargo_responsavel,
            email_responsavel=email_responsavel,
            telefone_responsavel=telefone_responsavel,
            unidade_uniesp=unidade_uniesp,
            diretor_responsavel=diretor_responsavel,
            data_assinatura=data_assinatura,
            observacoes=observacoes,
            caminho_arquivo_pdf=caminho_arquivo,
            status=status
        )
        
        db.session.add(novoConvenio)
        db.session.commit()

        if arquivo and caminho_arquivo:
            arquivo.save(caminho_arquivo)
        
        return jsonify({'message': 'Convênio inserido com sucesso'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Listar todos os Convênios
@app.route('/convenio', methods=['GET'])
def get_all():
    convenios = Convenios.query.all()
    return jsonify([convenio.as_dict() for convenio in convenios])

# Listar Convênio por id
@app.route('/convenio/<uuid:convenio_id>', methods=['GET'])
def get_convenio(convenio_id):
    convenio = Convenios.query.get_or_404(convenio_id)
    return jsonify(convenio.as_dict())

# Editar Convênio (por id)
@app.route('/convenio/<uuid:convenio_id>', methods=['PATCH', 'POST'])
def update_convenio(convenio_id):
    convenio = Convenios.query.get_or_404(convenio_id)
    
    try:
        # Se a requisição for JSON (apenas dados de texto)
        if request.is_json:
            data = request.get_json()
        # Se for um formulário multipart (dados e/ou arquivo)
        else:
            data = request.form
        
        # Itera sobre os dados recebidos para atualizar o convênio
        for key, value in data.items():
            if key == 'data_assinatura':
                if value:
                    setattr(convenio, key, datetime.strptime(value, '%Y-%m-%d').date())
                else:
                    setattr(convenio, key, None)
            elif key == 'status':
                if value in [e.value for e in ConvenioStatus]:
                    setattr(convenio, key, ConvenioStatus(value))
            elif key in ['qtd_funcionarios', 'qtd_associados', 'qtd_sindicalizados']:
                setattr(convenio, key, int(value))
            else:
                setattr(convenio, key, value)
        
        # Verifica se um novo arquivo foi enviado para substituição
        if 'caminho_arquivo_pdf' in request.files:
            arquivo = request.files['caminho_arquivo_pdf']
            if arquivo and allowed_file(arquivo.filename):
                # Apaga o arquivo antigo se ele existir
                if convenio.caminho_arquivo_pdf and os.path.exists(convenio.caminho_arquivo_pdf):
                    os.remove(convenio.caminho_arquivo_pdf)

                # Salva o novo arquivo
                nome_seguro = secure_filename(arquivo.filename)
                nome_arquivo_unico = str(uuid.uuid4()) + "_" + nome_seguro
                caminho_salvo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo_unico)
                arquivo.save(caminho_salvo)
                setattr(convenio, 'caminho_arquivo_pdf', caminho_salvo)

        db.session.commit()
        return jsonify({'message': 'Convênio atualizado com sucesso'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Excluir Convênio (por id)
@app.route('/convenio/<uuid:convenio_id>', methods=['DELETE'])
def delete(convenio_id):
    convenio = Convenios.query.get_or_404(convenio_id)

    # Apaga o arquivo associado antes de excluir o registro do banco
    if convenio.caminho_arquivo_pdf and os.path.exists(convenio.caminho_arquivo_pdf):
        os.remove(convenio.caminho_arquivo_pdf)

    db.session.delete(convenio)
    db.session.commit()
    return jsonify({'message': 'Convênio removido com sucesso'})

# Cria as tabelas do banco de dados ao iniciar o app
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')