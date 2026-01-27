import os
from pymongo import MongoClient
from rag.embeddings import embed_text

# Variável de cache para a conexão
_collection = None

def _get_collection():
    """
    Conecta ao Mongo apenas quando necessário.
    """
    global _collection
    
    if _collection is None:
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise RuntimeError("Variável de ambiente MONGO_URI não definida")
            
        client = MongoClient(uri)
        db = client["chatbot_facom"]
        _collection = db["professores"]
        
    return _collection

def search_professor_semantico(query: str, top_k: int = 3):
    # 1. Obtém a collection aqui dentro (Lazy Load)
    collection = _get_collection()

    embedding = embed_text(query)

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index_professores",
                "path": "vector_embedding",
                "queryVector": embedding,
                "numCandidates": 50,
                "limit": top_k
            }
        }
    ]

    return list(collection.aggregate(pipeline))