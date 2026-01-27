from rag.prompts.institutional import build_institutional_prompt
# futuramente:
# from rag.prompts.disciplina import build_disciplina_prompt
# from rag.prompts.professor import build_professor_prompt
# from rag.prompts.mixed import build_mixed_prompt


def answer_with_llm(
    pergunta: str,
    contexto: str,
    categoria: str,
    llm_client
) -> str:
    """
    Gera a resposta final usando o LLM,
    escolhendo o prompt correto com base na categoria.
    """

    if categoria == "INSTITUCIONAL":
        prompt = build_institutional_prompt(pergunta, contexto)

    # elif categoria == "SEMANTICA_DISCIPLINA":
    #     prompt = build_disciplina_prompt(pergunta, contexto)

    # elif categoria == "SEMANTICA_PROFESSOR":
    #     prompt = build_professor_prompt(pergunta, contexto)

    else:
        raise ValueError(f"Categoria sem prompt definido: {categoria}")

    response = llm_client.generate(
        prompt=prompt,
        temperature=0.0
    )

    return response.strip()
