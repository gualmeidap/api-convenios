[![English](https://img.shields.io/badge/English-0A66C2?style=for-the-badge)](README.md) [![Português](https://img.shields.io/badge/Portugu%C3%AAs-lightgrey?style=for-the-badge)](README.pt-BR.md)

# Partnership Management System

Web system for managing partnership agreements (*convênios*), with authentication, role-based permissions, PDF data extraction (text + OCR) and analysis by a locally hosted LLM. It replaced spreadsheets and manual workflows with a single, auditable system.

## Stack

Python 3 · Flask · Flask-Login · Flask-Migrate · Flask-Mail · SQLAlchemy · PostgreSQL · pdfplumber · Tesseract OCR · Ollama

## How extraction works

1. The uploaded PDF is read with `pdfplumber`.
2. Pages with no text (scanned) fall through to OCR (Tesseract, `por`), so the expensive path only runs when needed.
3. The text goes to a local Ollama model, with the output forced into JSON.
4. The extracted fields fill in the agreement record.

## Permissions

| Role | Can |
|---|---|
| `admin` | create, edit and delete agreements; manage users; view the audit log |
| `diretor` | view and register agreements |

Every action is recorded in an audit log.

## Layout

```
app.py            Flask application
db.py             database connection
models/           SQLAlchemy models
routes/           routes for agreements, users and AI helpers
templates/        screens
migrations/       Alembic migrations
```

## Running it

```bash
python -m venv venv
venv\Scripts\activate        # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
```

Requirements: a running PostgreSQL, Tesseract installed, and Ollama with the `llama3.2` model. Set the `ADMIN_EMAIL` and `ADMIN_PASSWORD` environment variables before the first run: the admin user is created from them, and there is no built-in default credential.

```bash
python app.py     # http://127.0.0.1:8080
```
