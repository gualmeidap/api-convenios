from flask_wtf import FlaskForm
from sqlalchemy.dialects.postgresql import UUID, TEXT
from sqlalchemy import func
from db import db
from datetime import datetime
from enum import Enum as PyEnum
# Novos imports para autenticação
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Modelo de Usuário para Autenticação
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256))
    # Perfil do usuário
    role = db.Column(db.String(20), nullable=False, default='diretor')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Enum para os status do convênio
class ConvenioStatus(PyEnum):
    ativo = "ativo"
    rescindido = "rescindido"
    expirado = "expirado"

class Convenios(db.Model):
    __tablename__ = 'convenio'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    nome_conveniada = db.Column(db.String(255), nullable=False)
    cnpj = db.Column(db.String(255), nullable=False)
    nome_fantasia = db.Column(db.String(255), nullable=False)
    cidade = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(255), nullable=False)
    area_atuacao = db.Column(db.String(255), nullable=False)
    qtd_funcionarios = db.Column(db.Integer, nullable=False)
    qtd_associados = db.Column(db.Integer, nullable=False)
    qtd_sindicalizados = db.Column(db.Integer, nullable=False)
    responsavel_legal = db.Column(db.String(255), nullable=False)
    cargo_responsavel = db.Column(db.String(255), nullable=False)
    email_responsavel = db.Column(db.String(255), nullable=False)
    telefone_responsavel = db.Column(db.String(255), nullable=False)
    unidade_uniesp = db.Column(db.String(255), nullable=False)
    diretor_responsavel = db.Column(db.String(255), nullable=False)
    diretor_responsavel_email = db.Column(db.String(255), nullable=True)
    data_assinatura = db.Column(db.Date, nullable=False)
    observacoes = db.Column(TEXT(), nullable=True)
    caminho_arquivo_pdf = db.Column(db.String(512), nullable=True)
    status = db.Column(db.Enum(ConvenioStatus), nullable=False)
    criado_em = db.Column(db.TIMESTAMP, nullable=False, default=func.now())
    atualizado_em = db.Column(db.TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())

    def as_dict(self):
        return {
            'id': str(self.id),
            'nome_conveniada': self.nome_conveniada,
            'cnpj': self.cnpj,
            'nome_fantasia': self.nome_fantasia,
            'cidade': self.cidade,
            'estado': self.estado,
            'area_atuacao': self.area_atuacao,
            'qtd_funcionarios': self.qtd_funcionarios,
            'qtd_associados': self.qtd_associados,
            'qtd_sindicalizados': self.qtd_sindicalizados,
            'responsavel_legal': self.responsavel_legal,
            'cargo_responsavel': self.cargo_responsavel,
            'email_responsavel': self.email_responsavel,
            'telefone_responsavel': self.telefone_responsavel,
            'unidade_uniesp': self.unidade_uniesp,
            'diretor_responsavel': self.diretor_responsavel,
            'diretor_responsavel_email': self.diretor_responsavel_email,
            'data_assinatura': self.data_assinatura.isoformat() if self.data_assinatura else None,
            'observacoes': self.observacoes,
            'caminho_arquivo_pdf': self.caminho_arquivo_pdf,
            'status': self.status.value,
            'criado_em': self.criado_em.isoformat(),
            'atualizado_em': self.atualizado_em.isoformat()
        }
    
# Modelo de Dados para o Log de Auditoria
class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    # Chave estrangeira e um relacionamento com a tabela de usuários
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))

    action = db.Column(db.String(50), nullable=False)     # Ação realizada (ex: 'CREATE', 'UPDATE', 'DELETE')
    record_id = db.Column(db.String(100), nullable=False) # O ID do registro de convênio/usuário que foi alterado
    table_name = db.Column(db.String(255), nullable=False) # O nome da tabela alterada 
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now()) # A data e hora da ação
    details = db.Column(db.String(1024), nullable=True) # Detalhes adicionais sobre a mudança

    def as_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username, # Retorna o nome de usuário
            'action': self.action,
            'record_id': str(self.record_id),
            'table_name': self.table_name,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'details': self.details
        }