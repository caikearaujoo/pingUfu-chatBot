import os
import certifi
from pymongo import MongoClient
from rag.embeddings import embed_text

_collection = None

def _get_collection():
    """Conecta ao Mongo usando certificados TLS com configurações otimizadas."""
    global _collection
    if _collection is None:
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise RuntimeError("Variável de ambiente MONGO_URI não definida no .env")

        client = MongoClient(
            uri,
            tlsCAFile=certifi.where(),
            tls=True,
            retryWrites=False,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )
        db = client["chatbot_facom"]
        _collection = db["professores"]
    return _collection

def search_professor_semantico(query: str, top_k: int = 3):
    collection = _get_collection()
    embedding = embed_text(query)

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index_professores", # Nome que está no seu Atlas
                "path": "vetor_unificado",           # Campo com os vetores
                "queryVector": embedding,
                "numCandidates": 50,
                "limit": top_k
            }
        }
    ]

    return list(collection.aggregate(pipeline))