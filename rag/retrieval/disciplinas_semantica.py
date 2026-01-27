import os
from pymongo import MongoClient
from rag.embeddings import embed_text

client = MongoClient(os.getenv("MONGO_URI"))
db = client["chatbot_facom"]
collection = db["disciplinas"]

def search_disciplina_semantica(query: str, top_k: int = 1):
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
