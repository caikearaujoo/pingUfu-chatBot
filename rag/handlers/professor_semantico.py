from rag.retrieval.professores import search_professor_semantico

def handle_professor_semantico(pergunta: str, routing: dict):
    docs = search_professor_semantico(pergunta)

    if not docs:
        return {"contexto": "", "sources": []}

    contexto = "\n\n".join(
        f"""
Professor: {d['prof_nome']}
Área: {d['prof_area']}
Pesquisa: {d['prof_pesquisa']}
"""
        for d in docs
    )

    return {
        "contexto": contexto.strip(),
        "sources": docs
    }
