from rag.retrieval.docs_inst import search_docs_institucionais


def handle_institucional(pergunta: str, routing: dict) -> dict:
    """
    Handler responsável por perguntas institucionais:
    regras, normas, resoluções, estágio, TCC, etc.
    """

    curso_alvo = routing.get("curso_alvo")

    # Buscar documentos relevantes
    docs = search_docs_institucionais(
        query=pergunta,
        curso_alvo=curso_alvo,
        top_k=5
    )

    if not docs:
        return {
            "answer": "Não encontrei documentos institucionais relevantes para responder sua pergunta.",
            "sources": []
        }

    # Montar contexto para o LLM responder
    contexto = "\n\n".join(
        f"[{doc['doc_titulo']} - pág {doc['pagina_origem']}]\n{doc['conteudo_chunk']}"
        for doc in docs
    )

    return {
        "contexto": contexto,
        "sources": docs
    }
