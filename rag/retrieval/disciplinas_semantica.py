import os
import certifi
from pymongo import MongoClient
from rag.embeddings import embed_text

# Variável global interna para guardar a conexão (cache)
_collection = None

def _get_collection():
    """
    Função auxiliar para conectar ao banco apenas quando necessário.
    Evita erro de conexão ao importar o arquivo.
    """
    global _collection

    if _collection is None:
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise RuntimeError("Variável de ambiente MONGO_URI não definida")

        client = MongoClient(
            uri,
            tlsCAFile=certifi.where(),
            tls=True,
            retryWrites=False,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )
        db = client["chatbot_facom"]
        _collection = db["disciplinas"]

    return _collection

def search_disciplina_semantica(query: str, top_k: int = 1):
    # 1. Obtém a collection aqui dentro (Lazy Load)
    collection = _get_collection()

    # 2. O resto do seu código continua IDENTICO
    embedding = embed_text(query)

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index_disciplinas",
                "path": "vector_embedding",
                "queryVector": embedding,
                "numCandidates": 50,
                "limit": top_k
            }
        }
    ]

    return list(collection.aggregate(pipeline))