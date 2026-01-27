import os
from pymongo import MongoClient

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
        _collection = db["disciplinas"]
        
    return _collection

def search_disciplina_estrutural(codigo: str | None = None, nome: str | None = None):
    # 1. Obtém a collection aqui dentro (Lazy Load)
    collection = _get_collection()

    query = {}

    if codigo:
        query["disciplina_codigo"] = codigo

    if nome:
        query["disciplina_nome"] = {"$regex": nome, "$options": "i"}

    return list(collection.find(query))