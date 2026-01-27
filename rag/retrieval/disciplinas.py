from pymongo import MongoClient
from rag.embeddings import embed_text

client = MongoClient("SUA_URI_MONGO")
db = client["chatbot_facom"]
collection = db["disciplinas"]


def search_disciplinas_semantica(query: str, curso_alvo: str | None, top_k: int = 5):
    query_embedding = embed_text(query)

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index_disciplinas",
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
                "curso.curso_sigla": curso_alvo
            }
        })

    results = list(collection.aggregate(pipeline))

    return [
        {
            "disciplina_nome": r["disciplina_nome"],
            "disciplina_codigo": r["disciplina_codigo"],
            "conteudo_semantico": r["conteudo_semantico"],
            "score": r.get("_score")
        }
        for r in results
    ]
