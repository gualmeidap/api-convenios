import shutil
from flask import Blueprint, abort, flash, redirect, render_template, request, jsonify, send_from_directory, url_for
from flask_login import login_required, current_user
from db import db
from models.convenios import AuditLog, Convenios, ConvenioStatus
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from routes.routes_user import role_required
from routes.ai_utils import extract_text_from_pdf, analyze_text_with_ollama
import traceback

# BLueprint de Convênios
convenio_bp = Blueprint('convenio_bp', __name__)

# Função auxiliar para verificar a extensão do arquivo
ALLOWED_EXTENSIONS = {'pdf'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Função auxiliar para enviar e-mail
def send_email(to_email, subject, body):
    from app import app, mail
    print("Tentando enviar e-mail...")
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

# --- Rotas de Visualização (Servindo HTML) ---

@convenio_bp.route('/convenio')
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

# Rota do processamento da IA

@convenio_bp.route('/processar_ia', methods=['POST'])
@login_required
@role_required(['admin', 'diretor'])
def processar_ia():
    """
    Rota exclusiva para processar o PDF e retornar JSON para o frontend.
    Nâo salva nada no banco de dados de convênios ainda.
    """
    from app import app

    if 'caminho_arquivo_pdf' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    arquivo = request.files['caminho_arquivo_pdf']

    if arquivo and allowed_file(arquivo.filename):
        print("Arquivo recebido.")
        try:
            # Salva temporariamente para leitura
            print("Salvando arquivo temporário...")
            nome_seguro = secure_filename(arquivo.filename)
            nome_unico = f"temp_{uuid.uuid4()}_{nome_seguro}"
            caminho_temp = os.path.join(app.config['UPLOAD_FOLDER'], nome_unico)
            arquivo.save(caminho_temp)
            print("Arquivo temporário salvo.")

            # Extração e Análise
            print("Extraindo texto do arquivo...")
            texto_extraido = extract_text_from_pdf(caminho_temp)
            print("Texto Extraído")

            # Prepara os dados do usuário logado (será incluído como nome e e-mail do diretor)
            info_diretor = {
                "diretor_responsavel": current_user.username,
                "diretor_responsavel_email": current_user.email
            }
            print(f"Nome e e-mail do usuário logado: {info_diretor}")

            print("Analisando texto extraído")
            resultado_ai = analyze_text_with_ollama(texto_extraido, user_info=info_diretor)
            print("\n--- Resultado Analisado pela IA ---")
            print(resultado_ai)

            # Retorna o caminho do arquivo e os dados para o frontend
            # O frontend deve guardar esse 'caminho_temp' para enviar no POST final
            return jsonify({
                'success': True,
                'dados_sugeridos': resultado_ai,
                'temp_file_path': caminho_temp
            })
        
        except Exception as e:
            traceback.print_exc()
            return jsonify({'error': f'Falha no processamento: {str(e)}'}), 500
        
    return jsonify({'error': 'Arquivo inválido'}), 400

# Cadastrar Convênio
@convenio_bp.route('/convenio', methods=['POST'])
@login_required
@role_required(['admin', 'diretor'])
def adicionar_convenio():
    from app import app, mail

    print("Iniciando rota: adicionar_convenio")

    try:
        caminho_final = None

        # 1. Lógica de Arquivo: Prioridade para arquivo já processado pela IA
        temp_path = request.form.get('temp_file_path')
        arquivo_novo = request.files.get('caminho_arquivo_pdf')

        if temp_path and os.path.exists(temp_path):
            # Move o arquivo temporário para o nome definitivo (removendo o prefixo temp_)
            nome_final = os.path.basename(temp_path).replace('temp_', '')
            caminho_final = os.path.join(app.config['UPLOAD_FOLDER'], nome_final)
            shutil.move(temp_path, caminho_final)
        elif arquivo_novo and allowed_file(arquivo_novo.filename):
            # Caso o usuário tenha feito upload mas não passou pela rota de IA
            nome_seguro = secure_filename(arquivo_novo.filename)
            nome_unico = f"{uuid.uuid4()}_{nome_seguro}"
            caminho_final = os.path.join(app.config['UPLOAD_FOLDER'], nome_unico)
            arquivo_novo.save(caminho_final)

        # 2. Coleta de Dados do Formulário (O que o usuário revisou/editou)
        def get_field(field_name, field_type=str):
            # Tenta pegar do form primeiro
            val = request.form.get(field_name)
            if val is None or val.strip() == "":
                return None
            try:
                return field_type(val)
            except:
                return None
        
        # Obtém os dados de texto do formulário (request.form)
        nome_conveniada = get_field('nome_conveniada')
        cnpj = get_field('cnpj')
        nome_fantasia = get_field('nome_fantasia')
        cidade = get_field('cidade')
        estado = get_field('estado')
        area_atuacao = get_field('area_atuacao')
        qtd_funcionarios = get_field('qtd_funcionarios', field_type=int)
        qtd_associados = get_field('qtd_associados', field_type=int)
        qtd_sindicalizados = get_field('qtd_sindicalizados', field_type=int)
        responsavel_legal = get_field('responsavel_legal')
        cargo_responsavel = get_field('cargo_responsavel')
        email_responsavel = get_field('email_responsavel')
        telefone_responsavel = get_field('telefone_responsavel')
        unidade_uniesp = get_field('unidade_uniesp')
        diretor_responsavel = get_field('diretor_responsavel')
        diretor_responsavel_email = get_field('diretor_responsavel_email')
        observacoes = get_field('observacoes')
        
        # Tratamento especial para Data e Status (Date/Enums objetcts)
        print("Processando data de assinatura")
        data_assinatura_str = request.form.get('data_assinatura')
        data_assinatura = None
        if data_assinatura_str and data_assinatura_str.strip() != "":
            try:
                # Tenta converter a string da data
                data_assinatura = datetime.strptime(data_assinatura_str, '%Y-%m-%d').date()
                #print(f"Data convertida: {data_assinatura}")
            except:
                try: data_assinatura = datetime.strptime(data_assinatura_str, '%d-%m-%Y').date()
                except: print("Erro ao converter data")
                traceback.print_exc()
        
        # --- Alteração para garantir minúsculas no status, se houver valor ---
        print("Processando status")
        status_str = request.form.get('status')
        status = None
        if status_str:
            status_lower = status_str.lower()
            if status_lower in [e.value for e in ConvenioStatus]:
                status = ConvenioStatus(status_lower)
                print(f"Status definido: {status}")
            else:
                print(f"Status inválido recebido: {status_str}")

        # Cria o novo objeto Convenios
        print("Criando objeto Convenios")
        novoConvenio = Convenios(
            user_id=current_user.id, # Associa o convênio ao ID do usuário logado
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
            caminho_arquivo_pdf=caminho_final,
            status=status
        )
        
        print("Salvando convênio no banco")
        db.session.add(novoConvenio)
        db.session.commit()
        print("Convênio salvo com ID {novoConvenio.id}")

        # --- Lógica de Envio de E-mail ---
        if diretor_responsavel_email:
            print("Disparando e-mail para diretor")
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
        print("Criando log de auditoria")
        log_entry = AuditLog(
            user=current_user,
            action='CREATE',
            record_id=novoConvenio.id,
            table_name='convenio',
            details=f"Novo convênio '{nome_conveniada}' criado."
        )
        db.session.add(log_entry)
        db.session.commit()
        print("Log de auditoria salvo")
        # --- FIM DO LOG DE AUDITORIA ---
        
        # Redireciona o usuário para a página de visualização após o sucesso
        print("Rota finalizada com sucesso")
        flash('Convênio inserido com sucesso!')
        return redirect(url_for('convenio_bp.visualizar_convenios'))

    except Exception:
        print("Erro geral da rota adicionar_convenio")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': 'Erro interno ao cadastrar convênio'}), 500
    
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
@role_required(['admin', 'diretor'])
def update_convenio(convenio_id):
    convenio = Convenios.query.get_or_404(convenio_id)
    from app import app

    # Permite edição se for Admin OU se o usuário logado for o criador do convênio
    is_admin = current_user.role == 'admin'
    is_owner = convenio.user_id == current_user.id

    if not is_admin and not is_owner:
        abort(403) # Acesso negado
    
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

    # Permite exclusão se for Admin OU se o usuário logado for o criador do convênio
    is_admin = current_user.role == 'admin'
    is_owner = convenio.user_id == current_user.id

    if not is_admin and not is_owner:
        abort(403) # Acesso negado

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
@convenio_bp.route('/logs_auditoria', methods=['GET'])
@login_required
@role_required(['admin'])
def get_logs_auditoria():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return jsonify([log.as_dict() for log in logs])