from rag.retrieval.disciplinas_semantica import search_disciplina_semantica

def handle_disciplina_semantica(pergunta: str, routing: dict):
    docs = search_disciplina_semantica(pergunta)

    if not docs:
        return {"contexto": "", "sources": []}

    doc = docs[0]

    contexto = f"""
Disciplina: {doc['disciplina_nome']}
Objetivo: {doc['disciplina_obj']}
Ementa: {doc['disciplina_ementa']}
Bibliografia: {doc['disciplina_bibliografia']}
"""

    return {
        "contexto": contexto.strip(),
        "sources": [doc]
    }
