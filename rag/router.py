
from rag.classifier import classify_question
from rag.answer_engine import answer_with_llm

from rag.handlers.institucional import handle_institucional
from rag.handlers.disciplina_semantica import handle_disciplina_semantica
from rag.handlers.disciplina_estrutural import handle_disciplina_estrutural
from rag.handlers.professor_semantico import handle_professor_semantico
from rag.handlers.mixed import handle_mixed_query


def route_question(pergunta: str, llm_client):
    """
    Roteia a pergunta, recupera contexto e gera resposta final via LLM
    """

    routing = classify_question(pergunta, llm_client)
    categoria = routing.get("categoria")

    print(f"\n🧠 [DEBUG] A IA classificou a pergunta como: {categoria}")

    # Seleciona o handler
    if categoria == "INSTITUCIONAL":
        result = handle_institucional(pergunta, routing)

    elif categoria == "SEMANTICA_DISCIPLINA":
        result = handle_disciplina_semantica(pergunta, routing)

    elif categoria == "ESTRUTURAL_DISCIPLINA":
        result = handle_disciplina_estrutural(pergunta, routing)

    elif categoria == "SEMANTICA_PROFESSOR":
        result = handle_professor_semantico(pergunta, routing)

    elif categoria == "MISTA":
        result = handle_mixed_query(pergunta, routing)

    else:
        raise ValueError(f"Categoria desconhecida: {categoria}")

    # Se o handler não achou nada
    if "contexto" not in result or not result["contexto"]:
        return {
            "answer": "Não encontrei informações suficientes nos documentos oficiais.",
            "sources": []
        }

    # Chamada CENTRALIZADA ao LLM
    answer = answer_with_llm(
        pergunta=pergunta,
        contexto=result["contexto"],
        categoria=categoria,
        llm_client=llm_client
    )

    # Resposta final padronizada
    return {
        "answer": answer,
        "sources": result.get("sources", []),
        "categoria": categoria
    }
