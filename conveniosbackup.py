# ARQUIVO USADO PARA SALVR A CLASSE CONVENIOS,
# POIS A ORIGINAL ESTAVA SENDO USADA PARA TESTES COM APENAS ALGUMAS COLUNAS

# from sqlalchemy.dialects.postgresql import UUID, TEXT
# from sqlalchemy import func
# from db import db

# class Convenios(db.Model):
#     __tablename__ = 'convenio'

    # id = db.Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    # nome_conveniada = db.Column(db.String(255), nullable=False)
    # cnpj = db.Column(db.String(255), nullable=False)
    # nome_fantasia = db.Column(db.String(255), nullable=False)
    # cidade = db.Column(db.String(255), nullable=False)
    # estado = db.Column(db.String(255), nullable=False)
    # area_atuacao = db.Column(db.String(255), nullable=False)
    # qtd_funcionarios = db.Column(db.Integer, nullable=False)
    # qtd_associados = db.Column(db.Integer, nullable=False)
    # qtd_sindicalizados = db.Column(db.Integer, nullable=False)
    # responsavel_legal = db.Column(db.String(255), nullable=False)
    # cargo_responsavel = db.Column(db.String(255), nullable=False)
    # email_responsavel = db.Column(db.String(255), nullable=False)
    # telefone_responsavel = db.Column(db.String(255), nullable=False)
    # unidade_uniesp = db.Column(db.String(255), nullable=False)
    # diretor_responsavel = db.Column(db.String(255), nullable=False)
    # data_assinatura = db.Column(db.Date, nullable=False)
    # observacoes = db.Column(TEXT(), nullable=False)
    # caminho_arquivo_pdf = db.Column(TEXT(), nullable=False)
    # status = db.Column(db.Enum(), nullable=False)
    # criado_em = db.Column(db.TIMESTAMP, nullable=False)
    # atualizado_em = db.Column(db.TIMESTAMP, nullable=False)

    # def as_dict(self):
    #     return {
    #         'id': str(self.id),
    #         'nome_conveniada': self.nome_conveniada,
    #         'cidade': self.cidade,
    #         'estado': self.estado,
    #         'unidade_uniesp': self.unidade_uniesp,
    #         'observacoes': self.observacoes
    #     }