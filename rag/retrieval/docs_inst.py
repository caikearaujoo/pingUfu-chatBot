import os
from pymongo import MongoClient
from rag.embeddings import embed_text

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError("Variável de ambiente MONGO_URI não definida")

client = MongoClient(MONGO_URI)
db = client["chatbot_facom"]
collection = db["DocsInst"]


def search_docs_institucionais(
    query: str,
    curso_alvo: str | None = None,
    top_k: int = 5
):
    """
    Busca vetorial em documentos institucionais (MongoDB Atlas Vector Search)
    """

    query_embedding = embed_text(query)

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index_docsinst",
                "path": "vector_embedding",
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": top_k,
                "filter": (
                    {"curso_alvo": curso_alvo}
                    if curso_alvo else {}
                )
            }
        }
    ]

    results = list(collection.aggregate(pipeline))

    return [
        {
            "doc_titulo": r["doc_titulo"],
            "pagina_origem": r["pagina_origem"],
            "conteudo_chunk": r["conteudo_chunk"],
            "doc_tipo": r.get("doc_tipo"),
            "score": r.get("_score", r.get("score"))
        }
        for r in results
    ]
