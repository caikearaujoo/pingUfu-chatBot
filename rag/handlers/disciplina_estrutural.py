from rag.retrieval.disciplinas_estrutural import search_disciplina_estrutural

def handle_disciplina_estrutural(pergunta: str, routing: dict):
    codigo = routing.get("codigo_disciplina")
    nome = routing.get("disciplina_nome")

    docs = search_disciplina_estrutural(codigo=codigo, nome=nome)

    if not docs:
        return {"contexto": "", "sources": []}

    partes_contexto = []
    
    # Vamos pegar até os 3 primeiros resultados pra não poluir muito
    for doc in docs[:3]:
        texto = f"""
Código: {doc.get('disciplina_codigo', 'N/A')}
Disciplina: {doc.get('disciplina_nome', 'N/A')}
Carga horária: {doc.get('disciplina_ch', 'N/A')}
Pré-requisitos: {doc.get('preRequisitos', [])}
Curso: {doc.get('curso', {}).get('curso_sigla', 'N/A')}
"""
        partes_contexto.append(texto.strip())

    return {
        "contexto": "\n\n---\n\n".join(partes_contexto),
        "sources": docs[:3]
    }