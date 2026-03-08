from rag.retrieval.disciplinas_semantica import search_disciplina_semantica

def handle_disciplina_semantica(pergunta: str, routing: dict):
    # Pedindo pro banco trazer as 5 disciplinas que mais combinam com a pergunta
    docs = search_disciplina_semantica(pergunta, top_k=3)

    if not docs:
        return {"contexto": "", "sources": []}

    partes_contexto = []
    
    # Agora a gente faz um loop para pegar os dados de TODAS as matérias que voltaram
    for doc in docs:
        texto = f"""
Disciplina: {doc.get('disciplina_nome', 'Desconhecido')}
Objetivo: {doc.get('disciplina_obj', '')}
Ementa: {doc.get('disciplina_ementa', '')}
"""
        partes_contexto.append(texto.strip())

    # Junta todas as 5 matérias, separando por uma linhazinha
    contexto_final = "\n\n---\n\n".join(partes_contexto)

    return {
        "contexto": contexto_final,
        "sources": docs # Retorna a lista inteira pra aparecer lá no final do chat
    }