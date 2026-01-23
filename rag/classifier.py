import json


def build_router_prompt(pergunta: str) -> str:
    return f"""
Você é um classificador de perguntas de um sistema acadêmico universitário.

Classifique a pergunta abaixo em UMA das categorias:

- INSTITUCIONAL
- SEMANTICA_DISCIPLINA
- ESTRUTURAL_DISCIPLINA
- SEMANTICA_PROFESSOR
- MISTA

Extraia também:
- curso_alvo (se houver: BCC, BSI, etc)
- intencao principal (ex: regra, conteudo, carga_horaria, professor)

Responda APENAS em JSON válido.

Pergunta:
"{pergunta}"
"""


def classify_question(pergunta: str, llm_client) -> dict:
    prompt = build_router_prompt(pergunta)

    response = llm_client.generate(
        prompt=prompt,
        temperature=0.0
    )

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        raise ValueError("Classificador retornou JSON inválido")
