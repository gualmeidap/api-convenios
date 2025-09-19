from flask_wtf import FlaskForm
from sqlalchemy.dialects.postgresql import UUID, TEXT
from sqlalchemy import func
from db import db
from datetime import datetime
from enum import Enum as PyEnum

# Enum para os status do convênio
class ConvenioStatus(PyEnum):
    ativo = "Ativo"
    rescindido = "Rescindido"
    expirado = "Expirado"

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
            'data_assinatura': self.data_assinatura.isoformat() if self.data_assinatura else None,
            'observacoes': self.observacoes,
            'caminho_arquivo_pdf': self.caminho_arquivo_pdf,
            'status': self.status.value,
            'criado_em': self.criado_em.isoformat(),
            'atualizado_em': self.atualizado_em.isoformat()
        }