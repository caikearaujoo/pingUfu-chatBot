from rag.handlers.disciplina_semantica import handle_disciplina_semantica
from rag.handlers.professor_semantico import handle_professor_semantico
from rag.handlers.institucional import handle_institucional

def handle_mixed_query(pergunta: str, routing: dict):
    partes = []
    fontes_mistas = [] # Criamos uma lista pra guardar as fontes

    for handler in [
        handle_disciplina_semantica,
        handle_professor_semantico,
        handle_institucional
    ]:
        result = handler(pergunta, routing)
        if result.get("contexto"):
            partes.append(result["contexto"])
        if result.get("sources"):
            fontes_mistas.extend(result["sources"]) # Junta as fontes de todos

    if not partes:
        return {"contexto": "", "sources": []}

    return {
        "contexto": "\n\n".join(partes),
        "sources": fontes_mistas # Retorna a lista cheia
    }