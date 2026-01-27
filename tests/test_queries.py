import sys
import os
import json
from unittest.mock import patch, MagicMock

# 1. Configura Chave FALSA
os.environ["MONGO_URI"] = "mongodb+srv://fake:fake@cluster0.fake.mongodb.net/"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rag.router import route_question

# --- MOCK DO LLM ---
class MockLLMClient:
    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        if "Classifique" in prompt:
            if "estágio" in prompt: return json.dumps({"categoria": "INSTITUCIONAL", "curso_alvo": "BCC"})
            if "aprende" in prompt: return json.dumps({"categoria": "SEMANTICA_DISCIPLINA", "curso_alvo": "BCC"})
            if "pré-requisito" in prompt: return json.dumps({"categoria": "ESTRUTURAL_DISCIPLINA"})
            if "pesquisa" in prompt: return json.dumps({"categoria": "SEMANTICA_PROFESSOR"})
            if "IA" in prompt: return json.dumps({"categoria": "MISTA"})
            return json.dumps({"categoria": "INSTITUCIONAL"})
        return "RESPOSTA MOCK: O sistema processou sua pergunta com sucesso."

TEST_QUESTIONS = [
    "Quantas horas de estágio obrigatório?",           # Institucional
    "O que se aprende em Estruturas de Dados?",        # Semântica Disciplina
    "Quais os pré-requisitos de GBC034?",              # Estrutural (NOVO)
    "Qual professor pesquisa sobre IA?",               # Professor (NOVO)
]

@patch("rag.handlers.institucional.search_docs_institucionais")
@patch("rag.handlers.disciplina_semantica.search_disciplina_semantica")
@patch("rag.handlers.disciplina_estrutural.search_disciplina_estrutural")
@patch("rag.handlers.professor_semantico.search_professor_semantico")
def run_tests(mock_prof, mock_disc_est, mock_disc_sem, mock_inst):
    
    # 1. Institucional
    mock_inst.return_value = [{
        "doc_titulo": "Resolução de Estágio 2024", 
        "conteudo_completo": "O estágio exige 300 horas...",
        "link": "http://ufu.br/pdf",
        "metadados": {"ano": 2024}
    }]

    # 2. Disciplina Semântica
    mock_disc_sem.return_value = [{
        "disciplina_nome": "Estruturas de Dados 1",
        "disciplina_codigo": "GBC024",
        "disciplina_obj": "Capacitar o aluno na implementação de estruturas lineares.",
        "disciplina_ementa": "Alocação dinâmica, Tipos Abstratos de Dados, Listas, Pilhas, Filas.",
        "disciplina_programa": "Unidade 1: Ponteiros...", 
        "disciplina_bibliografia": "Cormen, T. H. Algoritmos...", 
        "metadados": {"nome": "Estruturas de Dados", "codigo": "GBC024"}
    }]
    
    # 3. Disciplina Estrutural
    mock_disc_est.return_value = [{
        "disciplina_nome": "POO 2", 
        "disciplina_codigo": "GBC034",
        "pre_requisitos": "POO 1",
        "carga_horaria": 60
    }]
    
    # 4. Professor (AGORA COM 'prof_pesquisa')
    mock_prof.return_value = [{
        "prof_nome": "Prof. Dr. Alan Turing",
        "prof_area": "Inteligência Artificial",
        "prof_email": "turing@ufu.br",
        "prof_laboratorio": "Lab de IA",
        "prof_pesquisa": "Redes Neurais, Machine Learning e Computabilidade.", # <--- O CAMPO QUE FALTAVA
        "prof_lattes": "http://lattes.cnpq.br/1234", # Prevenção extra
        "conteudo": "Pesquisa em Redes Neurais e Computabilidade."
    }]

    client_simulado = MockLLMClient()
    
    print("Rodando testes com BANCO MOCKADO (Versão Final)...")
    
    for pergunta in TEST_QUESTIONS:
        print("-" * 50)
        try:
            result = route_question(pergunta, client_simulado)
            print(f"✅ Pergunta: {pergunta}")
            print(f"   Categoria: {result['categoria']}")
            print(f"   Resposta: {result['answer'][:100]}...") 
        except Exception as e:
            print(f"❌ Erro na pergunta '{pergunta}': {e}")
            import traceback
            traceback.print_exc()
if __name__ == "__main__":
    run_tests()