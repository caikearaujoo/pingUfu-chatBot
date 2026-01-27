import os
from pymongo import MongoClient
from rag.embeddings import embed_text
from bson import ObjectId

# Variável global para cachear a conexão (Singleton simplificado)
_db_client = None

def _get_collections():
    """
    Conecta ao Mongo apenas quando necessário.
    Retorna as collections (filhos, pai).
    """
    global _db_client
    
    uri = os.getenv("MONGO_URI")
    if not uri:
        raise RuntimeError("Variável de ambiente MONGO_URI não definida")

    if _db_client is None:
        _db_client = MongoClient(uri)
    
    db = _db_client["chatbot_facom"]
    return db["documentos_filhos"], db["documentos_pai"]


def search_docs_institucionais(
    query: str,
    curso_alvo: str | None = None
) -> list[dict]:
    """
    Busca institucional com Parent–Child Indexing.
    """
    
    # 1. Obtém as conexões agora (Lazy Load)
    col_filhos, col_pai = _get_collections()

    query_embedding = embed_text(query)

    # 2. Busca vetorial nos filhos
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index_docsinst_filhos",
                "path": "vector_embedding",
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": 3  # SUGESTÃO: Aumentei para 3 para ter mais chance de acerto
            }
        }
    ]

    filhos = list(col_filhos.aggregate(pipeline))

    if not filhos:
        return []

    # Pegamos o primeiro (top 1) por enquanto
    parent_id = filhos[0].get("parent_id")

    if not parent_id:
        return []

    # 3. Busca o documento pai
    pai = col_pai.find_one(
        {"_id": ObjectId(parent_id)}
    )

    if not pai:
        return []

    # 4. Filtro opcional por curso
    if curso_alvo:
        cursos_doc = pai.get("metadados", {}).get("curso_alvo", [])
        # Normaliza para lista se não for
        if not isinstance(cursos_doc, list):
            cursos_doc = [cursos_doc]
            
        if curso_alvo not in cursos_doc and "TODOS" not in cursos_doc:
            return []

    # 5. Retorno padronizado
    return [
        {
            "doc_titulo": pai.get("doc_titulo"),
            "tipo": pai.get("tipo"),
            "conteudo_completo": pai.get("conteudo_completo"),
            "metadados": pai.get("metadados")
        }
    ]