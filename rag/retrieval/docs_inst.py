import os
from pymongo import MongoClient
from rag.embeddings import embed_text
from bson import ObjectId

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError("Variável de ambiente MONGO_URI não definida")

client = MongoClient(MONGO_URI)
db = client["chatbot_facom"]

collection_filhos = db["documentos_filhos"]
collection_pai = db["documentos_pai"]


def search_docs_institucionais(
    query: str,
    curso_alvo: str | None = None
) -> list[dict]:
    """
    Busca institucional com Parent–Child Indexing.

    Fluxo:
    1. Busca vetorial nos chunks filhos
    2. Recupera o parent_id mais relevante
    3. Retorna o documento pai completo (1 artigo)
    """

    query_embedding = embed_text(query)

    # 1. Busca vetorial nos filhos
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index_docsinst_filhos",
                "path": "vector_embedding",
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": 1
            }
        }
    ]

    filhos = list(collection_filhos.aggregate(pipeline))

    if not filhos:
        return []

    parent_id = filhos[0].get("parent_id")

    if not parent_id:
        return []

    # 2. Busca o documento pai
    pai = collection_pai.find_one(
        {"_id": ObjectId(parent_id)}
    )

    if not pai:
        return []

    # 3. Filtro opcional por curso
    if curso_alvo:
        cursos_doc = pai.get("metadados", {}).get("curso_alvo", [])
        if curso_alvo not in cursos_doc and "TODOS" not in cursos_doc:
            return []

    # 4. Retorno padronizado
    return [
        {
            "doc_titulo": pai.get("doc_titulo"),
            "tipo": pai.get("tipo"),
            "conteudo_completo": pai.get("conteudo_completo"),
            "metadados": pai.get("metadados")
        }
    ]
