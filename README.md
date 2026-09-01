# 📑 Gerenciador de Convênios UNIESP

Sistema web para gerenciamento de convênios, com autenticação, controle de permissões e auditoria de ações. Desenvolvido em **Flask** com base em perfis de acesso (`admin` e `diretor`).

---

## ✅ Tecnologias Utilizadas

- Python 3.x  
- Flask  
- Flask-Login  
- Flask-Migrate  
- Flask-Mail  
- SQLAlchemy  
- PostgreSQL

---

## ✅ Estrutura Geral do Projeto

<pre>
api-convenios/
│
├── app.py
├── db.py
├── models/
│ ├── __init__.py
│ └── convenios.py
├── routes/
│ ├── __init__.py
│ ├── routes_user.py
│ └── routes_convenio.py
├── templates/
│ ├── index.html
│ ├── login.html
│ ├── register.html
│ ├── visualizador_logs_auditoria.html
│ ├── visualizar_convenios.html
│ └── visualizar_usuarios.html
├── uploads/
├── migrations/
└── requirements.txt
</pre>

---

## ✅ Instalação e Execução
---
### 1️⃣ Criar e ativar um ambiente virtual (opcional)

```bash
python -m venv venv
```
#### Windows:
```bash
venv\Scripts\activate
```
#### Linux/Mac:
```bash
source venv/bin/activate
```
---
### 2️⃣ Instalar dependências

```bash
pip install -r requirements.txt
```
---
### 3️⃣ Configurar Banco de Dados

Certifique-se de que o PostgreSQL está rodando e que a base de dados indicada no app.py existe:

```bash
postgresql://postgres:postgres@localhost:5432/termos
```
---
### 4️⃣ Rodar o projeto

```bash
python app.py
```
Por padrão, o app sobe em:

```cpp
http://127.0.0.1:8080
```
---
### ✅ Observações Importantes
Ao iniciar o sistema pela primeira vez, um usuário admin é criado automaticamente a
partir das variáveis de ambiente `ADMIN_EMAIL` e `ADMIN_PASSWORD`. Defina as duas
antes da primeira execução — não há credencial padrão embutida, e o sistema não sobe
sem elas.

Diretório uploads/ armazena os PDFs enviados.

Permissões:

admin → criar, editar, excluir convênios, gerenciar usuários e visualizar log de auditoria

diretor → apenas visualizar e cadastrar convênios