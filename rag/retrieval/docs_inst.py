from pymongo import MongoClient
from rag.embeddings import embed_text

client = MongoClient("SUA_URI_MONGO")
db = client["chatbot_facom"]
collection = db["DocsInst"]


def search_docs_institucionais(query: str, curso_alvo: str | None, top_k: int = 5):
    """
    Faz busca vetorial em documentos institucionais
    """

    query_embedding = embed_text(query)

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index_docsinst",
                "path": "vector_embedding",
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": top_k
            }
        }
    ]

    if curso_alvo:
        pipeline.append({
            "$match": {
                "curso_alvo": curso_alvo
            }
        })

    results = list(collection.aggregate(pipeline))

    return [
        {
            "doc_titulo": r["doc_titulo"],
            "pagina_origem": r["pagina_origem"],
            "conteudo_chunk": r["conteudo_chunk"],
            "doc_tipo": r.get("doc_tipo"),
            "score": r.get("_score")
        }
        for r in results
    ]
