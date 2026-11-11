> 🇺🇸 [English version](README.md)

# Sistema de Gestão de Convênios

Sistema web para gerenciamento de convênios, com autenticação, controle de permissões, extração de dados de PDFs (texto + OCR) e análise por LLM local. Substituiu planilhas e fluxos manuais por um sistema único e auditável.

## Tecnologias

Python 3 · Flask · Flask-Login · Flask-Migrate · Flask-Mail · SQLAlchemy · PostgreSQL · pdfplumber · Tesseract OCR · Ollama

## Como funciona a extração

1. O PDF enviado é lido com `pdfplumber`.
2. Páginas sem texto (digitalizadas) passam pelo OCR (Tesseract, `por`).
3. O texto vai para o Ollama local, com saída forçada em JSON.
4. Os campos extraídos preenchem o cadastro do convênio.

## Permissões

| Perfil | Pode |
|---|---|
| `admin` | criar, editar e excluir convênios; gerenciar usuários; ver o log de auditoria |
| `diretor` | visualizar e cadastrar convênios |

## Estrutura

```
app.py            aplicação Flask
db.py             conexão com o banco
models/           modelos SQLAlchemy
routes/           rotas de convênios, usuários e utilitários de IA
templates/        telas
migrations/       migrações Alembic
```

## Como rodar

```bash
python -m venv venv
venv\Scripts\activate        # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
```

Requisitos: PostgreSQL rodando, Tesseract instalado e o Ollama com o modelo `llama3.2`. Defina as variáveis `ADMIN_EMAIL` e `ADMIN_PASSWORD` antes da primeira execução: o usuário admin é criado a partir delas e não há credencial padrão embutida.

```bash
python app.py     # http://127.0.0.1:8080
```
