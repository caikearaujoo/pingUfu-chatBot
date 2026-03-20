import os
import certifi
from pymongo import MongoClient
from rag.embeddings import embed_text

_collection = None

def _get_collection():
    """Conecta ao Mongo com segurança usando certificados TLS e configurações otimizadas."""
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
        _collection = db["disciplinas"]

    return _collection

def search_disciplina_estrutural(codigo: str = None, nome: str = None):
    """
    Busca informações estruturais (pré-requisitos, CH) de uma disciplina.
    """
    collection = _get_collection()

    # 1. BUSCA POR CÓDIGO (Ex: GBC024)
    # Usamos o find tradicional porque o código é um identificador exato.
    if codigo:
        print(f"🔍 [DEBUG] Buscando código exato: {codigo}")
        return list(collection.find({"disciplina_codigo": {"$regex": f"^{codigo}$", "$options": "i"}}))

    # 2. BUSCA POR NOME (Ex: "Estrutura de Dados")
    # Usamos o Vector Search para lidar com erros de digitação ou nomes incompletos.
    if nome:
        print(f"🧠 [DEBUG] Buscando nome via Vetores: {nome}")
        embedding = embed_text(nome)
        
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index_disciplinas", # Nome que confirmamos no seu print do Atlas
                    "path": "vector_embedding",         # Campo criado pelo populacao.py
                    "queryVector": embedding,
                    "numCandidates": 50,
                    "limit": 3
                }
            }
        ]
        return list(collection.aggregate(pipeline))

    return []