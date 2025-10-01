from functools import wraps
from flask import Blueprint, flash, redirect, render_template, request, jsonify, url_for
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from db import db
from models.convenios import User, AuditLog

# 1. Criação do Blueprint: O prefixo de URL aqui será vazio ('/') ou '/usuarios' se quisermos isolar.
user_bp = Blueprint('user_bp', __name__)

# --- Decorador Personalizado de Permissão ---

# Decorador personalizado para verificar o perfil do usuário logado.
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash("Você não tem permissão para acessar esta página.")
                # Redireciona para a página principal de convênios, se a permissão falhar
                return redirect(url_for('convenio_bp.visualizar_convenios'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Rotas de Login e Logout ---

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('convenio_bp.visualizar_convenios'))
    
    if request.method == 'POST':
        # Correção: Campo 'email' substituindo o campo 'username' configurado no login.html
        email_input = request.form.get('email')
        password = request.form.get('password')

        # A busca continua flexível, procurando o valor fornecido (email_input) tanto no campo 'username' quanto no campo 'email'.
        user = User.query.filter(or_(User.username == email_input, User.email == email_input)).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('convenio_bp.visualizar_convenios'))
        else:
            flash("Usuário ou senha inválidos.")
            return redirect(url_for('user_bp.login'))
        
    return render_template('login.html')

@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('user_bp.login'))

# --- Rotas de Gerenciamento de Usuários (Admin) ---

@user_bp.route('/register', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if User.query.filter_by(email=email).first():
            flash("Endereço de e-mail já registrado.")
            return redirect(url_for('user_bp.register'))
        
        new_user = User(email=email, username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.sesson.commit()
        flash(f"Usuário {username} criado com sucesso!")
        return redirect(url_for('convenio_bp.visualizar_convenios'))
    
    return render_template('register.html')

# --- Rota para a página de visualização de usuários ---
@user_bp.route('/visualizar_usuarios')
@login_required
@role_required(['admin'])
def visualizar_usuarios():
    return render_template('visualizar_usuarios.html')

# --- Rota de API para obter todos os usuários ---
@user_bp.route('/users_api', methods=['GET'])
@login_required
@role_required(['admin'])
def get_users_api():
    users = User.query.all()
    # Retorna uma lista de dicionários com os dados dos usuários
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role
    } for user in users])

# --- Rota para editar um usuário ---
@user_bp.route('/users/<int:user_id>', methods=['PATCH'])
@login_required
@role_required(['admin'])
def update_user_api(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    
    try:
        # Verifica se o email já existe para outro usuário
        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Este e-mail já está em uso.'}), 400
            
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'role' in data:
            user.role = data['role']
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        db.session.commit()
        
        # Log de auditoria para a edição
        log_entry = AuditLog(
            user=current_user,
            action='UPDATE',
            record_id=str(user_id),
            table_name='user',
            details=f"Usuário '{user.username}' editado."
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({'message': 'Usuário atualizado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
# --- Nova rota para excluir um usuário ---
@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required(['admin'])
def delete_user_api(user_id):
    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        
        # Log de auditoria para a exclusão
        log_entry = AuditLog(
            user=current_user,
            action='DELETE',
            record_id=str(user_id),
            table_name='user',
            details=f"Usuário '{user.username}' excluído."
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({'message': 'Usuário removido com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@user_bp.route('/users/diretores_api', methods=['GET'])
@login_required
@role_required(['admin'])
def get_diretores_api():
    diretores = User.query.filter_by(role='diretor').all()
    return jsonify([{'id': diretor.id, 'username': diretor.username} for diretor in diretores])