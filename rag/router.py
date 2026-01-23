from rag.classifier import classify_question

from rag.handlers.institucional import handle_institucional
from rag.handlers.disciplina_semantica import handle_disciplina_semantica
from rag.handlers.disciplina_estrutural import handle_disciplina_estrutural
from rag.handlers.professor_semantico import handle_professor_semantico
from rag.handlers.mixed import handle_mixed_query


def route_question(pergunta: str, llm_client):
    """
    Roteia a pergunta para o handler correto com base na classificação LLM
    """

    routing = classify_question(pergunta, llm_client)
    categoria = routing.get("categoria")

    if categoria == "INSTITUCIONAL":
        return handle_institucional(pergunta, routing)

    if categoria == "SEMANTICA_DISCIPLINA":
        return handle_disciplina_semantica(pergunta, routing)

    if categoria == "ESTRUTURAL_DISCIPLINA":
        return handle_disciplina_estrutural(pergunta, routing)

    if categoria == "SEMANTICA_PROFESSOR":
        return handle_professor_semantico(pergunta, routing)

    if categoria == "MISTA":
        return handle_mixed_query(pergunta, routing)

    raise ValueError(f"Categoria desconhecida: {categoria}")
