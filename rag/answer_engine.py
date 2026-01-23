def build_institutional_prompt(pergunta: str, contexto: str) -> str:
    return f"""
Você é um assistente acadêmico da Universidade Federal de Uberlândia (UFU).

Responda à pergunta abaixo utilizando APENAS as informações fornecidas no contexto.
Se a informação não estiver explicitamente no contexto, diga que não encontrou a informação nos documentos oficiais.

Sempre:
- Seja claro e objetivo
- Use linguagem institucional
- Não invente informações
- Cite implicitamente os documentos quando relevante

Pergunta:
{pergunta}

Contexto:
{contexto}

Resposta:
"""
def answer_with_llm(
    pergunta: str,
    contexto: str,
    llm_client
) -> str:
    prompt = build_institutional_prompt(pergunta, contexto)

    response = llm_client.generate(
        prompt=prompt,
        temperature=0.0
    )

    return response.strip()
