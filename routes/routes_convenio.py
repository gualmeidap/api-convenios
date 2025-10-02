from flask import Blueprint, flash, redirect, render_template, request, jsonify, send_from_directory, url_for
from flask_login import login_required, current_user
from db import db
from models.convenios import AuditLog, Convenios, ConvenioStatus
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from routes.routes_user import role_required

# BLueprint de Convênios
convenio_bp = Blueprint('convenio_bp', __name__)

# Função auxiliar para verificar a extensão do arquivo
ALLOWED_EXTENSIONS = {'pdf'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Rotas de Visualização (Servindo HTML) ---

@convenio_bp.route('/')
@login_required
@role_required(['admin', 'diretor'])
def index():
    return render_template('index.html')

@convenio_bp.route('/visualizar')
@login_required
@role_required(['admin', 'diretor'])
def visualizar_convenios():
    return render_template('visualizar_convenios.html')

@convenio_bp.route('/visualizar_logs')
@login_required
@role_required(['admin'])
def visualizar_logs():
    return render_template('visualizador_logs_auditoria.html')

# --- Rotas de API para Convênios (CRUD) ---

@convenio_bp.route('/convenios_api', methods=['GET'])
@login_required
@role_required(['admin', 'diretor'])
def get_convenios_api():
    convenios = Convenios.query.all()
    convenios_list = [convenio.as_dict() for convenio in convenios]
    return jsonify(convenios_list)

# Cadastrar Convênio
@convenio_bp.route('/convenio', methods=['POST'])
@login_required
@role_required(['admin', 'diretor'])
def adicionar_convenio():
    from app import app, mail

    # Função auxiliar para enviar e-mail
    def send_email(to_email, subject, body):
        try:
            with app.app_context():
                msg = Message(subject,
                            sender=app.config['MAIL_USERNAME'],
                            recipients=[to_email])
                msg.body = body
                mail.send(msg)
                print(f"E-mail enviado com sucesso para {to_email}.")
                return True
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")
            return False
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
        diretor_responsavel_email = request.form.get('diretor_responsavel_email')
        data_assinatura_str = request.form.get('data_assinatura')
        observacoes = request.form.get('observacoes')
        status_str = request.form.get('status')
        
        # Converte tipos
        data_assinatura = datetime.strptime(data_assinatura_str, '%Y-%m-%d').date() if data_assinatura_str else None
        status = ConvenioStatus(status_str) if status_str in [e.value for e in ConvenioStatus] else None
        
        # Prepara o arquivo
        arquivo = request.files.get('caminho_arquivo_pdf')
        caminho_arquivo = None
        if arquivo and allowed_file(arquivo.filename):
            nome_seguro = secure_filename(arquivo.filename)
            nome_arquivo_unico = str(uuid.uuid4()) + "_" + nome_seguro
            caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo_unico)

        # Cria o novo objeto Convenios
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
            diretor_responsavel_email=diretor_responsavel_email,
            data_assinatura=data_assinatura,
            observacoes=observacoes,
            caminho_arquivo_pdf=caminho_arquivo,
            status=status
        )
        
        db.session.add(novoConvenio)
        db.session.commit()

        # --- Lógica de Envio de E-mail ---
        if diretor_responsavel_email:
            assunto = f"Nova Parceria Cadastrada - {nome_conveniada}"
            corpo = f"""Prezado(a) Diretor(a),\n\n
Informamos que a unidade {unidade_uniesp} firmou nova parceria com a empresa {nome_conveniada},
com benefícios educacionais válidos a partir de {data_assinatura.strftime('%d/%m/%Y')}.

Termo anexado: [https://uniespvestibular.com.br/convenios/]


Atenciosamente,
Equipe UNIESP"""
            send_email(diretor_responsavel_email, assunto, corpo)
        # --- Fim da Lógica de E-mail ---

        # --- LOG DE AUDITORIA: Ação de Criação ---
        log_entry = AuditLog(
            user=current_user,
            action='CREATE',
            record_id=novoConvenio.id,
            table_name='convenio',
            details=f"Novo convênio '{nome_conveniada}' criado."
        )
        db.session.add(log_entry)
        db.session.commit()
        # --- FIM DO LOG DE AUDITORIA ---

        if arquivo and caminho_arquivo:
            arquivo.save(caminho_arquivo)
        
        # Redireciona o usuário para a página de visualização após o sucesso
        flash('Convênio inserido com sucesso!')
        return redirect(url_for('visualizar_convenios'))

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
# Listar Convênio por id
@convenio_bp.route('/convenio/<uuid:convenio_id>', methods=['GET'])
@login_required
@role_required(['admin', 'diretor'])
def get_convenio(convenio_id):
    convenio = Convenios.query.get_or_404(convenio_id)
    return jsonify(convenio.as_dict())

# Editar Convênio (por id)
@convenio_bp.route('/convenio/<uuid:convenio_id>', methods=['PATCH', 'POST'])
@login_required
@role_required(['admin'])
def update_convenio(convenio_id):
    convenio = Convenios.query.get_or_404(convenio_id)
    from app import app # Acesso ao config do app
    
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        print(f"DEBUG: Dados recebidos para atualização do Convênio {convenio_id}: {data}") # Log de debug
        
        # Itera sobre os dados recebidos para atualizar o convênio
        for key, value in data.items():

            # Garante que None (ou seja, campos vazios) não causem erros de string
            if value is None or value == '':
                value = None 

            if key == 'data_assinatura':
                if value:
                    setattr(convenio, key, datetime.strptime(value, '%Y-%m-%d').date())
                else:
                    setattr(convenio, key, None)
            elif key == 'status':
                print(f"DEBUG STATUS: Tentando processar status. Valor recebido: '{value}'") # Log de debug específico

                # Só tenta processar se o valor não for None (ou seja, se o campo veio na requisição)
                if value:
                    # Aplica a correção defensiva novamente: garante minúsculas
                    status_value_lower = value.lower()
                    
                    # Verifica se o valor minúsculo é válido no Enum
                    if status_value_lower in [e.value for e in ConvenioStatus]:
                        setattr(convenio, key, ConvenioStatus(status_value_lower))
                        print(f"DEBUG STATUS: Status alterado com sucesso para: {status_value_lower}")
                    else:
                        print(f"ERRO DE VALIDAÇÃO: Valor '{value}' não é um status válido. Ignorando atualização de status.")
                else:
                    print("DEBUG STATUS: Valor do status recebido está vazio ou nulo. Nenhuma alteração de status.")

            elif key in ['qtd_funcionarios', 'qtd_associados', 'qtd_sindicalizados']:
                if value is not None:
                    setattr(convenio, key, int(value))
            
            # Atualiza todos os outros campos de texto/string
            elif value is not None:
                setattr(convenio, key, value)
        
        # Verifica se um novo arquivo foi enviado para substituição
        if 'documento' in request.files:
            arquivo = request.files['documento']
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

        # --- LOG DE AUDITORIA: Ação de Atualização ---
        log_entry = AuditLog(
            user=current_user,
            action='UPDATE',
            record_id=convenio_id,
            table_name='convenio',
            details=f"Convênio '{convenio.nome_conveniada}' atualizado."
        )
        db.session.add(log_entry)
        db.session.commit()
        # --- FIM DO LOG DE AUDITORIA ---
        
        flash('Convênio atualizado com sucesso!', 'success')
        return jsonify({'message': 'Convênio atualizado com sucesso'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
# Excluir Convênio (por id)
@convenio_bp.route('/convenio/<uuid:convenio_id>', methods=['DELETE'])
@login_required
@role_required(['admin'])
def delete(convenio_id):
    convenio = Convenios.query.get_or_404(convenio_id)
    
    from app import app

    # --- LOG DE AUDITORIA: Ação de Exclusão ---
    log_entry = AuditLog(
        user=current_user,
        action='DELETE',
        record_id=convenio_id,
        table_name='convenio',
        details=f"Convênio '{convenio.nome_conveniada}' excluído."
    )
    db.session.add(log_entry)
    db.session.commit()
    # --- FIM DO LOG DE AUDITORIA ---

    # Apaga o arquivo associado antes de excluir o registro do banco
    if convenio.caminho_arquivo_pdf and os.path.exists(convenio.caminho_arquivo_pdf):
        os.remove(convenio.caminho_arquivo_pdf)

    db.session.delete(convenio)
    db.session.commit()
    flash('Convênio removido com sucesso!', 'success')
    return jsonify({'message': 'Convênio removido com sucesso'})

# Rota para servir o PDF
@convenio_bp.route('/uploads/<path:filename>')
@login_required
def download_file(filename):
    from app import app
    # Retorna o arquivo solicitado do diretório de uploads
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rota para visualizar os Logs de Auditoria
@convenio_bp.route('/logs_auditoria_api', methods=['GET'])
@login_required
@role_required(['admin'])
def get_logs_auditoria():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return jsonify([log.as_dict() for log in logs])