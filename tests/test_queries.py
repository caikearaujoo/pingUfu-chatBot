import sys
import os
import json
from unittest.mock import patch, MagicMock

# 1. Configura Chave FALSA para garantir que nenhuma validação de ambiente trave
os.environ["MONGO_URI"] = "mongodb+srv://fake:fake@cluster0.fake.mongodb.net/"

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rag.router import route_question

# --- MOCK DO LLM ---
class MockLLMClient:
    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        # Responde JSON se for classificação
        if "Classifique" in prompt:
            if "estágio" in prompt: return json.dumps({"categoria": "INSTITUCIONAL", "curso_alvo": "BCC"})
            if "aprende" in prompt: return json.dumps({"categoria": "SEMANTICA_DISCIPLINA", "curso_alvo": "BCC"})
            if "pré-requisito" in prompt: return json.dumps({"categoria": "ESTRUTURAL_DISCIPLINA"})
            if "IA" in prompt: return json.dumps({"categoria": "MISTA"})
            return json.dumps({"categoria": "INSTITUCIONAL"})
        
        # Responde texto se for a resposta final
        return "RESPOSTA MOCK: O sistema processou sua pergunta com sucesso."

# --- PERGUNTAS DE TESTE ---
TEST_QUESTIONS = [
    "Quantas horas de estágio obrigatório?",
    "O que se aprende em Estruturas de Dados?",
]

# --- 2. A MÁGICA DO PATCH (Impede a conexão real com o Mongo) ---
# Adicione aqui os paths para TODAS as funções de busca que seu router usa
@patch("rag.handlers.institucional.search_docs_institucionais")
@patch("rag.handlers.disciplina_semantica.search_disciplina_semantica") # Ajuste o nome se necessário
def run_tests(mock_disc_search, mock_inst_search):
    
    # Configura o retorno falso do banco
    mock_inst_search.return_value = [{"conteudo_completo": "O estágio exige 300 horas..."}]
    mock_disc_search.return_value = [{"conteudo": "Aprende-se listas, pilhas e filas..."}]

    client_simulado = MockLLMClient()
    
    print("Rodando testes com BANCO MOCKADO (Seguro)...")
    
    for pergunta in TEST_QUESTIONS:
        print("-" * 50)
        try:
            result = route_question(pergunta, client_simulado)
            print(f"✅ Pergunta: {pergunta}")
            print(f"   Categoria: {result['categoria']}")
            print(f"   Resposta: {result['answer']}")
        except Exception as e:
            print(f"❌ Erro na pergunta '{pergunta}': {e}")

if __name__ == "__main__":
    run_tests()