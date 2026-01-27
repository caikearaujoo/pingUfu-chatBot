import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))
db = client["chatbot_facom"]
collection = db["disciplinas"]

def search_disciplina_estrutural(codigo: str | None = None, nome: str | None = None):
    query = {}

    if codigo:
        query["disciplina_codigo"] = codigo

    if nome:
        query["disciplina_nome"] = {"$regex": nome, "$options": "i"}

    return list(collection.find(query))
