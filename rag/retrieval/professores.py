import os
from pymongo import MongoClient
from rag.embeddings import embed_text

client = MongoClient(os.getenv("MONGO_URI"))
db = client["chatbot_facom"]
collection = db["professores"]

def search_professor_semantico(query: str, top_k: int = 3):
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
