from flask import Flask, redirect, url_for
from flask.cli import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from db import db
from models.convenios import AuditLog, Convenios, ConvenioStatus, User
import os
from datetime import datetime
from flask_mail import Mail, Message
from routes.routes_user import user_bp
from routes.routes_convenio import convenio_bp

load_dotenv()

app = Flask(__name__)

# --- Configurações Básicas ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/termos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads') 
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# --- Configuração do Flask-Mail ---
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.office365.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
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
        # Credenciais do admin inicial vêm do ambiente (.env) — nunca do código.
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')

        admin_user = User.query.filter_by(username='admin').first()
        
        # 1. Cria o usuário 'admin' se ele não existir
        if not admin_user:
            if not admin_email or not admin_password:
                raise SystemExit(
                    "Defina ADMIN_EMAIL e ADMIN_PASSWORD (no .env ou no ambiente) antes "
                    "da primeira execução: são as credenciais do admin inicial."
                )
            print("Criando usuário 'admin' padrão...")
            # Adiciona o campo 'email' que é necessário para a autenticação/recuperação de senha.
            # Presume-se que o modelo User tenha o campo 'email'.
            admin_user = User(username='admin', role='admin', email=admin_email)
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            print(f"Usuário 'admin' criado com sucesso com email: {admin_email}")
        
        # 2. Se o usuário 'admin' existir, mas estiver sem e-mail, atualiza
        else:
            # Tenta acessar o atributo 'email'. Se o modelo User não tiver este atributo,
            # esta linha pode falhar na inicialização do app.
            if not hasattr(admin_user, 'email') or not admin_user.email:
                 if not admin_email:
                     raise SystemExit(
                         "O usuário 'admin' existe sem e-mail. Defina ADMIN_EMAIL para completá-lo."
                     )
                 print("Atualizando email do usuário 'admin' existente...")
                 # Tenta adicionar/atualizar o campo email
                 setattr(admin_user, 'email', admin_email)
                 db.session.commit()
                 print(f"Email do usuário 'admin' atualizado com sucesso para: {admin_email}")
    
    app.run(debug=True, port=8080, host='0.0.0.0')