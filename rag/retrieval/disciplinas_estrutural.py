import os
from pymongo import MongoClient
# Agora vamos importar a nossa ferramenta de vetores aqui também!
from rag.embeddings import embed_text 

_collection = None

def _get_collection():
    """Conecta ao Mongo apenas quando necessário."""
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
    collection = _get_collection()

    # 1. Se o aluno perguntar o CÓDIGO exato (ex: GBC012), a busca por texto (regex) é melhor
    if codigo:
        return list(collection.find({"disciplina_codigo": {"$regex": codigo, "$options": "i"}}))

    # 2. Se o aluno perguntar pelo NOME (ex: Geometria Analitica), usamos os Vetores!
    # Assim o bot ignora falta de acentos, erros de digitação e acha a matéria certa.
    if nome:
        embedding = embed_text(nome)
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index_disciplinas",
                    "path": "vector_embedding",
                    "queryVector": embedding,
                    "numCandidates": 50,
                    "limit": 3
                }
            }
        ]
        return list(collection.aggregate(pipeline))

    return []