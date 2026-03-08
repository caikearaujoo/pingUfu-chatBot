import json
import re

def build_router_prompt(pergunta: str) -> str:
    return f"""
Você é um classificador de perguntas de um sistema acadêmico universitário.

Classifique a pergunta abaixo em UMA das categorias:

- INSTITUCIONAL (Editais, normas, datas, regras gerais, TCC, estágio)
- SEMANTICA_DISCIPLINA (O que se aprende, ementa, objetivos)
- ESTRUTURAL_DISCIPLINA (Pré-requisitos, código da matéria, fluxo)
- SEMANTICA_PROFESSOR (Área de pesquisa, e-mail, laboratório)
- MISTA (Quando misturar dois assuntos)

Extraia também:
- curso_alvo (se houver: BCC, BSI, etc)
- intencao (ex: regra, conteudo, carga_horaria, professor)
- disciplina_nome (se a pergunta for sobre uma matéria)
- codigo_disciplina (se a pergunta citar o código)

Responda APENAS em JSON válido, sem markdown.

Pergunta:
"{pergunta}"
"""

def extract_json_secure(text: str) -> dict:
    """Tenta limpar a resposta do Gemini para extrair o JSON puro."""
    try:
        # Tentativa 1: Limpeza simples de Markdown
        clean_text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except json.JSONDecodeError:
        # Tentativa 2: Busca por Regex (Acha o primeiro { ... })
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Se falhar tudo
        raise ValueError(f"Não foi possível extrair JSON da resposta: {text}")

def classify_question(pergunta: str, llm_client) -> dict:
    prompt = build_router_prompt(pergunta)

    response = llm_client.generate(
        prompt=prompt,
        temperature=0.0
    )

    try:
        # Usa a função segura de extração
        return extract_json_secure(response)
        
    except Exception as e:
        print(f"⚠️ Erro no classificador: {e}. Usando fallback.")
        # Fallback seguro para não travar o bot
        return {
            "categoria": "INSTITUCIONAL", 
            "curso_alvo": None, 
            "intencao": "geral"
        }