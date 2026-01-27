from rag.retrieval.disciplinas import search_disciplinas_semantica


def handle_disciplina_semantica(pergunta: str, routing: dict) -> dict:
    """
    Handler para perguntas sobre conteúdo e aprendizado de disciplinas
    """

    curso_alvo = routing.get("curso_alvo")

    docs = search_disciplinas_semantica(
        query=pergunta,
        curso_alvo=curso_alvo,
        top_k=5
    )

    if not docs:
        return {
            "contexto": "",
            "sources": []
        }

    contexto = "\n\n".join(
        f"[{doc['disciplina_nome']} - {doc['disciplina_codigo']}]\n{doc['conteudo_semantico']}"
        for doc in docs
    )

    return {
        "contexto": contexto,
        "sources": docs
    }
