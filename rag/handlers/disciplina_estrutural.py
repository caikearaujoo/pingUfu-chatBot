from rag.retrieval.disciplinas_estrutural import search_disciplina_estrutural

def handle_disciplina_estrutural(pergunta: str, routing: dict):
    codigo = routing.get("codigo_disciplina")
    nome = routing.get("disciplina_nome")

    docs = search_disciplina_estrutural(codigo=codigo, nome=nome)

    if not docs:
        return {"contexto": "", "sources": []}

    doc = docs[0]

    contexto = f"""
Código: {doc.get('disciplina_codigo')}
Carga horária: {doc.get('disciplina_ch')}
Pré-requisitos: {doc.get('preRequisitos')}
Curso: {doc.get('curso_sigla')}
"""

    return {
        "contexto": contexto.strip(),
        "sources": [doc]
    }
