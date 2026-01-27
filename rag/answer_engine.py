from rag.prompts.institutional import build_institutional_prompt
from rag.prompts.disciplina import build_disciplina_prompt
from rag.prompts.professor import build_professor_prompt
from rag.prompts.mixed import build_mixed_prompt


PROMPT_REGISTRY = {
    "INSTITUCIONAL": build_institutional_prompt,
    "SEMANTICA_DISCIPLINA": build_disciplina_prompt,
    "ESTRUTURAL_DISCIPLINA": build_disciplina_prompt,
    "SEMANTICA_PROFESSOR": build_professor_prompt,
    "MISTA": build_mixed_prompt,
}

def answer_with_llm(
    pergunta: str,
    contexto: str,
    categoria: str,
    llm_client
) -> str:
    """
    Gera a resposta final usando o LLM com prompt específico por categoria.
    """

    prompt_builder = PROMPT_REGISTRY.get(categoria)

    if not prompt_builder:
        raise ValueError(f"Categoria sem prompt definido: {categoria}")

    prompt = prompt_builder(pergunta, contexto)

    response = llm_client.generate(
        prompt=prompt,
        temperature=0.0
    )

    return response.strip()
