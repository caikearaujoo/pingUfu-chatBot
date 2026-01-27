from rag.retrieval.docs_inst import search_docs_institucionais


def handle_institucional(pergunta: str, routing: dict) -> dict:
    """
    Handler responsável por perguntas institucionais:
    regras, normas, resoluções, estágio, TCC, etc.

    Regra:
    - Sempre retorna UM artigo completo
    - Nunca retorna chunks
    - Não chama LLM
    """

    curso_alvo = routing.get("curso_alvo")

    # Busca institucional (parent–child)
    docs = search_docs_institucionais(
        query=pergunta,
        curso_alvo=curso_alvo
    )

    if not docs:
        return {
            "contexto": "",
            "sources": []
        }

    doc = docs[0]

    # Contexto institucional íntegro
    contexto = (
        f"[{doc['doc_titulo']}]\n\n"
        f"{doc['conteudo_completo']}"
    )

    return {
        "contexto": contexto,
        "sources": [
            {
                "doc_titulo": doc["doc_titulo"],
                "tipo": doc.get("tipo"),
                "metadados": doc.get("metadados")
            }
        ]
    }
