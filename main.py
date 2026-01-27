import os
import sys
import json
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

# Adiciona a raiz ao path para garantir os imports
sys.path.append(os.path.dirname(__file__))

from rag.router import route_question

# --- Cores para o Terminal (Fica bonitão) ---
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

# --- 1. Cliente REAL (Para quando você configurar a chave) ---
class OpenAIClient:
    def __init__(self):
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY não encontrada no .env")
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            print(f"{RED}Erro: Biblioteca 'openai' não instalada.{RESET}")
            print("Instale com: pip install openai")
            sys.exit(1)
        except ValueError as e:
            print(f"{RED}{e}{RESET}")
            sys.exit(1)

    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo", # Ou gpt-4o-mini
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        return response.choices[0].message.content

# --- 2. Cliente MOCK (Para testar o fluxo agora) ---
class MockClient:
    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        # Simula a classificação do Router
        if "Classifique" in prompt:
            if "estágio" in prompt: return json.dumps({"categoria": "INSTITUCIONAL", "curso_alvo": "BCC"})
            if "aprende" in prompt: return json.dumps({"categoria": "SEMANTICA_DISCIPLINA"})
            if "pré-requisito" in prompt: return json.dumps({"categoria": "ESTRUTURAL_DISCIPLINA"})
            if "pesquisa" in prompt: return json.dumps({"categoria": "SEMANTICA_PROFESSOR"})
            return json.dumps({"categoria": "MISTA"})
        
        # Simula a resposta final
        return (
            "🤖 [RESPOSTA SIMULADA]\n"
            "Com base nos documentos recuperados, o sistema funcionou!\n"
            "O contexto foi passado corretamente para o prompt."
        )

# --- CONFIGURAÇÃO ---
# Mude para True para usar o Mock, False para usar a OpenAI Real
USE_MOCK = True  

def main():
    print(f"{BOLD}🎓 Chatbot Acadêmico UFU/FACOM Iniciado{RESET}")
    print("---------------------------------------------")
    
    if USE_MOCK:
        print(f"{YELLOW}⚠️  Rodando em MODO MOCK (Sem custos, sem IA real){RESET}")
        
        # Ajustamos o Client Mock para entender sua pergunta
        class SmarterMockClient(MockClient):
            def generate(self, prompt: str, temperature: float = 0.0) -> str:
                # Força a categoria PROFESSOR se tiver a palavra "professor"
                if "Classifique" in prompt and "professor" in prompt.lower():
                    return json.dumps({"categoria": "SEMANTICA_PROFESSOR", "intencao": "buscar_docente"})
                return super().generate(prompt, temperature)

        client = SmarterMockClient()
        
        from unittest.mock import patch
        
        # 1. Dados Institucionais Falsos
        patcher1 = patch("rag.handlers.institucional.search_docs_institucionais", 
            return_value=[{
                "doc_titulo": "Doc Teste", 
                "conteudo_completo": "Conteúdo de teste...", 
                "link": "http://ufu.br", 
                "metadados": {"ano": 2025}
            }]
        )

        # 2. Dados de Disciplina Falsos (Completos)
        patcher2 = patch("rag.handlers.disciplina_semantica.search_disciplina_semantica", 
            return_value=[{
                "disciplina_nome": "Banco de Dados 1", 
                "disciplina_obj": "Aprender SQL e Modelagem.", 
                "disciplina_ementa": "Modelo ER, Relacional, Normalização.", 
                "disciplina_programa": "Semana 1: Intro...", 
                "disciplina_bibliografia": "Navathe, Elmasri...", 
                "disciplina_codigo": "GBC043",
                "metadados": {"nome": "Banco de Dados 1"}
            }]
        )

        # 3. Dados Estruturais Falsos
        patcher3 = patch("rag.handlers.disciplina_estrutural.search_disciplina_estrutural", 
            return_value=[{
                "disciplina_nome": "Banco de Dados 1",
                "disciplina_codigo": "GBC043",
                "pre_requisitos": "Estrutura de Dados"
            }]
        )

        # 4. Dados de Professor Falsos (AGORA COMPLETOS)
        patcher4 = patch("rag.handlers.professor_semantico.search_professor_semantico", 
            return_value=[{
                "prof_nome": "Prof. Dr. Mock", 
                "prof_pesquisa": "Banco de Dados e Big Data",
                "prof_area": "Ciência de Dados",                # <--- Faltava isso
                "prof_email": "mock@ufu.br",                    # <--- Faltava isso
                "prof_laboratorio": "LabData",                  # <--- Faltava isso
                "prof_lattes": "http://lattes.cnpq.br/0000",    # <--- Faltava isso
                "conteudo": "O professor atua na área de BD."
            }]
        )
        
        patcher1.start()
        patcher2.start()
        patcher3.start()
        patcher4.start()
    else:
        print(f"{GREEN}🚀 Rodando em MODO REAL (Conectado à OpenAI e MongoDB Atlas){RESET}")
        client = OpenAIClient()

    print("Digite 'sair' para encerrar.\n")

    while True:
        try:
            pergunta = input(f"{BLUE}Você: {RESET}").strip()
            
            if not pergunta:
                continue
                
            if pergunta.lower() in ["sair", "exit", "quit"]:
                print("Até logo! 👋")
                break

            print(f"{YELLOW}Processando...{RESET}")
            
            # --- O CORAÇÃO DO SISTEMA ---
            response = route_question(pergunta, client)
            # ---------------------------

            print(f"\n{GREEN}PingUfu Bot:{RESET}")
            print(response["answer"])
            
            if response.get("sources"):
                print(f"\n{BOLD}[Fontes Utilizadas]:{RESET}")
                for src in response["sources"]:
                    # Tenta pegar título ou nome, dependendo do tipo de fonte
                    titulo = src.get("doc_titulo") or src.get("disciplina_nome") or src.get("prof_nome") or "Fonte Desconhecida"
                    print(f"- {titulo}")
            
            print("-" * 50)

        except KeyboardInterrupt:
            print("\nEncerrando...")
            break
        except Exception as e:
            print(f"{RED}Erro inesperado: {e}{RESET}")

if __name__ == "__main__":
    main()