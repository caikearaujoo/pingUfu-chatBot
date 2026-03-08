from rag.retrieval.professores import search_professor_semantico

def handle_professor_semantico(pergunta: str, routing: dict):
    docs = search_professor_semantico(pergunta)

    if not docs:
        return {"contexto": "", "sources": []}

    contexto = "\n\n".join(
        f"""
Professor: {d.get('prof_nome', 'Desconhecido')}
Área: {d.get('prof_area', 'Não informada')}
Pesquisa: {d.get('prof_pesquisa', 'Não informada')}
"""
        for d in docs
    )

    return {
        "contexto": contexto.strip(),
        "sources": docs
    }
