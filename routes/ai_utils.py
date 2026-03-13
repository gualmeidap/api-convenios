import pdfplumber
import pytesseract
from PIL import Image
import io
import requests
import json
import re
import time
from typing import Optional, Dict

# Configurações
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"

def extract_text_from_pdf(file_path: str) -> str:
    all_text = []
    start_time = time.time()
    try:
        print(f"[DEBUG] Abrindo PDF: {file_path}")
        with pdfplumber.open(file_path) as pdf:
            if not pdf.pages:
                raise ValueError("PDF não contém páginas")

            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and len(text.strip()) > 100:
                    print(f"[DEBUG] Texto extraído via PDFPlumber na página {i}")
                    all_text.append(text)
                else:
                    print(f"[DEBUG] Página {i} parece imagem, iniciando OCR...")
                    img = page.to_image(resolution=200).original
                    ocr_text = pytesseract.image_to_string(img, lang='por')
                    print(f"[DEBUG] Texto extraído via OCR na página {i}:")
                    print(ocr_text[:1000], "\n---\n")
                    all_text.append(ocr_text)
                    
        print(f"[DEBUG] Extração d e{len(pdf.pages)} páginasconcluída em {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"[ERRO] Falha na extração do PDF: {str(e)}")
        return ""
    return "\n".join(all_text)

def analyze_text_with_ollama(text: str) -> Optional[Dict]:
    if not text:
        print("[AVISO] Texto vazio enviado para a IA.")
        return None
    
    start_time = time.time()
    prompt_text = text[:6000]

    # System Prompt simplificado para evitar confusão no modelo 3b
    system_prompt = """
        Você é um extrator de dados JSON especializado em convênios.
        Sua resposta deve ser APENAS um objeto JSON puro, sem markdown, sem blocos de código e sem explicações.
        Extraia os seguintes campos se encontrar:
        nome_conveniada (Razão Social)
        cnpj
        nome_fantasia
        cidade
        estado (UF)
        area_atuacao (Área de Atuação)
        qtd_funcionarios (Quantidade de Funcionários)
        qtd_associados (Quantidade de Associados)
        qtd_sindicalizados (Quantidade de Sindicalizados)
        responsavel_legal (Responsável pela Instituição)
        cargo_responsavel (Cargo)
        email_responsavel (Email do Responsável)
        telefone_responsavel (Telefone do Responsável)
        unidade_uniesp
        diretor_responsavel:
        diretor_responsavel_email:
        data_assinatura:
        Data de assinatura do documento.
        Procurar próximo de "(data) - ASSINATURA".
        Retornar no formato ISO: YYYY-MM-DD.
        data_validade:
        Data final de validade do convênio.
        Retornar no formato ISO: YYYY-MM-DD.
        Se o contrato for por tempo indeterminado ou não possuir data final, retornar "9999-12-31".
    """

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"Extraia os dados deste texto de convênio em JSON:\n\n{prompt_text}",
        "system": system_prompt,
        "stream": False,
        "format": "json", # FORÇA O OLLAMA A ENTREGAR JSON
        "options": {
            "temperature": 0,
            "num_predict": 800,
            "top_k": 20,
            "top_p": 0.9
        }
    }

    try:
        print(f"[DEBUG] Enviando para Ollama ({OLLAMA_MODEL})...")
        # Timeout de 120s é geralmente suficiente para o Qwen 3b local
        response = requests.post(OLLAMA_URL, json=payload, timeout=150)
        
        if response.status_code != 200:
            print(f"[ERRO] Ollama retornou status {response.status_code}: {response.text}")
            return None

        full_response = response.json()
        raw_content = full_response.get('response', '')
        
        print(f"[DEBUG] Resposta bruta da IA recebida ({len(raw_content)} chars)")

        # Tenta parsear diretamente já que usamos format: json
        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError:
            # Fallback para regex se o JSON vier sujo
            print("[AVISO] Falha no parse direto, tentando Regex...")
            clean_json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            if clean_json_match:
                data = json.loads(clean_json_match.group())
            else:
                raise ValueError("Não foi possível localizar JSON na resposta.")

        # Sanitização de campos inúteis
        blacklist = ["n/a", "não encontrado", "null", "none", "", "undefined"]
        final_data = {k: v for k, v in data.items() if str(v).lower() not in blacklist and v}
        
        print(f"[DEBUG] Análise concluída com sucesso em {time.time() - start_time:.2f}s")
        return final_data

    except requests.exceptions.Timeout:
        print("[ERRO] Timeout: O Ollama demorou demais para responder. Verifique o consumo de CPU/GPU.")
    except Exception as e:
        print(f"[ERRO] Geral no analyze_text_with_ollama: {str(e)}")
        
    return None