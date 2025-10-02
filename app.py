from flask import Flask, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from db import db
from models.convenios import AuditLog, Convenios, ConvenioStatus, User
import os
from datetime import datetime
from flask_mail import Mail, Message
from routes.routes_user import user_bp
from routes.routes_convenio import convenio_bp

app = Flask(__name__)

# --- Configurações Básicas ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/termos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads') 
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma-chave-secreta-muito-segura')

# --- Configuração do Flask-Mail ---
app.config['MAIL_SERVER'] = 'smtp.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('FLASK_MAIL_USERNAME', 'convenios.uniesp@uniesp.edu.br')
app.config['MAIL_PASSWORD'] = os.environ.get('FLASK_MAIL_PASSWORD', 'mudar@123')
mail = Mail(app)

# --- Inicialização de Extensões ---
db.init_app(app)
migrate = Migrate(app, db)

# --- Configuração do Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'user_bp.login'

@login_manager.user_loader
def load_user(user_id):
    # Função para carregar o usuário pelo ID, usada pelo Flask-Login
    return User.query.get(int(user_id))

# --- Rota Raiz Principal ---
# Redireciona a rota '/' (raiz) para a página de visualização de convênios, que está no Blueprint de convênios
@app.route('/')
@login_required
def root():
    return redirect(url_for('convenio_bp.visualizar_convenios'))

# --- Registro dos BLueprints ---
# Registra as rotas de usuário e autenticação (login, register, users_api)
app.register_blueprint(user_bp) 
# Registra as rotas de convênios (adicionar_convenio, visualizar, convenios_api, logs)
app.register_blueprint(convenio_bp)

# Bloco de inicialização do app
if __name__ == '__main__':
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        
        # 1. Cria o usuário 'admin' se ele não existir
        if not admin_user:
            print("Criando usuário 'admin' padrão...")
            # Adiciona o campo 'email' que é necessário para a autenticação/recuperação de senha.
            # Presume-se que o modelo User tenha o campo 'email'.
            admin_user = User(username='admin', role='admin', email='admin@uniesp.edu.br')
            admin_user.set_password('123456')
            db.session.add(admin_user)
            db.session.commit()
            print("Usuário 'admin' criado com sucesso com email: admin@uniesp.edu.br")
        
        # 2. Se o usuário 'admin' existir, mas estiver sem e-mail, atualiza
        else:
            # Tenta acessar o atributo 'email'. Se o modelo User não tiver este atributo,
            # esta linha pode falhar na inicialização do app.
            if not hasattr(admin_user, 'email') or not admin_user.email:
                 print("Atualizando email do usuário 'admin' existente...")
                 # Tenta adicionar/atualizar o campo email
                 setattr(admin_user, 'email', 'admin@uniesp.edu.br')
                 db.session.commit()
                 print("Email do usuário 'admin' atualizado com sucesso para: admin@uniesp.edu.br")
    
    app.run(debug=True, port=8080, host='0.0.0.0')