from functools import wraps
from flask import Flask, flash, redirect, render_template, request, jsonify, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from db import db
from models.convenios import Convenios, ConvenioStatus, User
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
# Chave secreta para a sessão (necessária para o Flask-Login)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma-chave-secreta-muito-segura')

db.init_app(app)
migrate = Migrate(app, db)

# --- Configuração do Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Decorador personalizado para verificar o perfil do usuário
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash("Você não tem permissão para acessar esta página.")
                return redirect(url_for('visualizar_convenios'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Rotas para Autenticação ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('visualizar_convenios'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('visualizar_convenios'))
        else:
            flash("Usuário ou senha inválidos.")
            return redirect(url_for('login'))
    
    # Formulário de login simples
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if User.query.filter_by(username=username).first():
            flash("Nome de usuário já existe.")
            return redirect(url_for('register'))
        
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f"Usuário {username} criado com sucesso!")
        return redirect(url_for('visualizar_convenios'))
    
    return render_template('register.html')

# Função auxiliar para verificar a extensão do arquivo
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Nova rota para servir o formulário HTML
@app.route('/')
@login_required
@role_required(['admin', 'diretor'])
def index():
    return render_template('index.html')

# Nova rota para visualizar os convênios (servindo o HTML)
@app.route('/visualizar')
@login_required
@role_required(['admin', 'diretor'])
def visualizar_convenios():
    return render_template('visualizar_convenios.html')

# Nova rota da API para obter os dados dos convênios em JSON
@app.route('/convenios_api', methods=['GET'])
@login_required
@role_required(['admin', 'diretor'])
def get_convenios_api():
    convenios = Convenios.query.all()
    convenios_list = [convenio.as_dict() for convenio in convenios]
    return jsonify(convenios_list)

# Cadastrar Convênio
@app.route('/convenio', methods=['POST'])
@login_required
@role_required(['admin', 'diretor'])
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
        
        # Redireciona o usuário para a página de visualização após o sucesso
        flash('Convênio inserido com sucesso!')
        return redirect(url_for('visualizar_convenios'))

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Listar todos os Convênios
@app.route('/convenio', methods=['GET'])
@login_required
@role_required(['admin', 'diretor'])
def get_all():
    convenios = Convenios.query.all()
    return jsonify([convenio.as_dict() for convenio in convenios])

# Listar Convênio por id
@app.route('/convenio/<uuid:convenio_id>', methods=['GET'])
@login_required
@role_required(['admin', 'diretor'])
def get_convenio(convenio_id):
    convenio = Convenios.query.get_or_404(convenio_id)
    return jsonify(convenio.as_dict())

# Editar Convênio (por id)
@app.route('/convenio/<uuid:convenio_id>', methods=['PATCH', 'POST'])
@login_required
@role_required(['admin'])
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
@login_required
@role_required(['admin'])
def delete(convenio_id):
    convenio = Convenios.query.get_or_404(convenio_id)

    # Apaga o arquivo associado antes de excluir o registro do banco
    if convenio.caminho_arquivo_pdf and os.path.exists(convenio.caminho_arquivo_pdf):
        os.remove(convenio.caminho_arquivo_pdf)

    db.session.delete(convenio)
    db.session.commit()
    return jsonify({'message': 'Convênio removido com sucesso'})

# Bloco de inicialização do app
if __name__ == '__main__':
    with app.app_context():
        # Verifique se o usuário 'admin' já existe para evitar erros
        if not User.query.filter_by(username='admin').first():
            print("Criando usuário 'admin' padrão...")
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('123456')
            db.session.add(admin_user)
            db.session.commit()
            print("Usuário 'admin' criado com sucesso.")
    
    app.run(debug=True, port=8080, host='0.0.0.0')