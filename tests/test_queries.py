# tests/test_queries.py

from rag.router import route_question   # ajuste o import
from rag.answer_engine import llm_client           # ajuste o import

TEST_QUESTIONS = [
    # INSTITUCIONAL
    "Quantas horas de estágio obrigatório são exigidas?",
    "O manual permite compensar horas de estágio?",

    # SEMANTICA_DISCIPLINA
    "O que se aprende em Estruturas de Dados?",
    "Essa disciplina é mais prática ou teórica?",

    # ESTRUTURAL_DISCIPLINA
    "Quais são os pré-requisitos de Estruturas de Dados?",
    "Quantas horas tem FACOM123?",

    # SEMANTICA_PROFESSOR
    "Quem trabalha com Inteligência Artificial?",
    "Qual professor pesquisa sistemas distribuídos?",

    # MISTA
    "Quais professores de IA podem orientar estágio obrigatório?",
    "Essa disciplina atende aos requisitos do estágio?"
]

def run_tests():
    for pergunta in TEST_QUESTIONS:
        print("=" * 60)
        print("Pergunta:", pergunta)

        result = route_question(pergunta, llm_client)

        print("Categoria detectada:", result.get("categoria"))
        print("Resposta:")
        print(result.get("answer"))

        sources = result.get("sources", [])
        print("Qtd de fontes:", len(sources))

if __name__ == "__main__":
    run_tests()
