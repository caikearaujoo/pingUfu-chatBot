import os
from functools import lru_cache

# ⚠️ IMPORTANTE:
# Não importamos HuggingFaceEmbeddings no topo
# Isso evita crash lento do SciPy no Windows

@lru_cache(maxsize=1)
def _load_embedding_model():
    """
    Carrega o modelo de embeddings UMA única vez.
    Lazy-load para evitar travar importações.
    """
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        cache_folder=os.path.join(os.getcwd(), ".hf_cache")
    )


def embed_text(text: str) -> list[float]:
    """
    Gera embedding para um único texto.
    """
    model = _load_embedding_model()
    return model.embed_query(text)


def embed_documents(texts: list[str]) -> list[list[float]]:
    """
    Gera embeddings para múltiplos textos.
    """
    model = _load_embedding_model()
    return model.embed_documents(texts)
