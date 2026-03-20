import os
import certifi
from pymongo import MongoClient
from rag.embeddings import embed_text
from bson import ObjectId

# Variável global para cachear a conexão (Singleton simplificado)
_db_client = None

def _get_collections():
    """
    Conecta ao Mongo com segurança e retorna as collections.
    """
    global _db_client
    
    uri = os.getenv("MONGO_URI")
    if not uri:
        raise RuntimeError("Variável de ambiente MONGO_URI não definida no .env")

    if _db_client is None:
        _db_client = MongoClient(
            uri,
            tlsCAFile=certifi.where(),
            tls=True,
            retryWrites=False,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        ) 
    db = _db_client["chatbot_facom"]
    return db["docsInstitucionais_chunks"], db["docsInstitucionais"]


def search_docs_institucionais(
    query: str,
    curso_alvo: str | None = None
) -> list[dict]:
    """
    Busca institucional com Parent–Child Indexing.
    """
    
    # 1. Obtém as conexões (Lazy Load)
    col_filhos, col_pai = _get_collections()

    query_embedding = embed_text(query)

    # 2. Busca vetorial nos filhos (chunks)
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index_docsinst_filhos", # Nome que confirmamos no seu Atlas
                "path": "vetor_chunk",                  # Campo definido no populacao.py
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": 3 
            }
        }
    ]

    filhos = list(col_filhos.aggregate(pipeline))

    if not filhos:
        return []

    # Pegamos o primeiro (top 1) para encontrar o documento pai original
    parent_id = filhos[0].get("parent_id")

    if not parent_id:
        return []

    # 3. Busca o documento pai completo para dar o contexto à IA
    pai = col_pai.find_one(
        {"_id": ObjectId(parent_id)}
    )

    if not pai:
        return []

    # 4. Filtro opcional por curso (BCC, BSI, etc)
    if curso_alvo:
        cursos_doc = pai.get("metadados", {}).get("curso_alvo", [])
        if not isinstance(cursos_doc, list):
            cursos_doc = [cursos_doc]
            
        if curso_alvo not in cursos_doc and "TODOS" not in cursos_doc:
            return []

    # 5. Retorno padronizado para o handler
    return [
        {
            "doc_titulo": pai.get("doc_nome"),
            "tipo": pai.get("tipo"),
            "conteudo_completo": pai.get("texto_completo"),
            "metadados": pai.get("metadados")
        }
    ]