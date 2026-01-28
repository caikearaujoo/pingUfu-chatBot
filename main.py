import os
import sys
import json
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# Adiciona a raiz ao path para garantir os imports
sys.path.append(os.path.dirname(__file__))

from rag.router import route_question

# --- Cores para o Terminal ---
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

# --- 1. Cliente GEMINI (O Cérebro Gratuito) ---
class GeminiClient:
    def __init__(self):
        try:
            # Importação específica do Google via LangChain
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY não encontrada no .env")
            
            
            self.llm = ChatGoogleGenerativeAI(
                model="models/gemini-2.5-flash",
                google_api_key=api_key,
                temperature=0
            )
        except ImportError:
            print(f"{RED}Erro: Biblioteca 'langchain-google-genai' não instalada.{RESET}")
            print("Instale com: pip install langchain-google-genai langchain-core")
            sys.exit(1)
        except ValueError as e:
            print(f"{RED}{e}{RESET}")
            sys.exit(1)

    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        # Atualiza a temperatura para a chamada atual
        self.llm.temperature = temperature
        
        # Invoca o modelo
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Erro na API do Google: {str(e)}"

# --- 2. Cliente MOCK (Para testes sem internet) ---
class MockClient:
    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        if "Classifique" in prompt:
            if "estágio" in prompt: return json.dumps({"categoria": "INSTITUCIONAL", "curso_alvo": "BCC"})
            if "aprende" in prompt: return json.dumps({"categoria": "SEMANTICA_DISCIPLINA"})
            if "pré-requisito" in prompt: return json.dumps({"categoria": "ESTRUTURAL_DISCIPLINA"})
            if "pesquisa" in prompt: return json.dumps({"categoria": "SEMANTICA_PROFESSOR"})
            return json.dumps({"categoria": "MISTA"})
        
        return (
            "🤖 [RESPOSTA MOCK]\n"
            "O sistema está rodando em modo de teste (Mock)."
        )

# --- CONFIGURAÇÃO ---
USE_MOCK = False  # <--- Deixe False para usar o Gemini Real

def main():
    print(f"{BOLD}🎓 Chatbot Acadêmico UFU/FACOM (Powered by Gemini){RESET}")
    print("-------------------------------------------------------")
    
    # Seleção do Cliente
    if USE_MOCK:
        print(f"{YELLOW}⚠️  Rodando em MODO MOCK (Sem IA real){RESET}")
        client = MockClient()
    else:
        print(f"{GREEN}🚀 Rodando em MODO REAL (Conectado ao Google Gemini){RESET}")
        client = GeminiClient()

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
            # Aqui passamos a pergunta e o cliente (Gemini) para o roteador
            response = route_question(pergunta, client)
            # ---------------------------

            print(f"\n{GREEN}PingUfu Bot:{RESET}")
            print(response["answer"])
            
            if response.get("sources"):
                print(f"\n{BOLD}[Fontes Utilizadas]:{RESET}")
                for src in response["sources"]:
                    # Tenta pegar título ou nome de forma segura
                    titulo = (src.get("doc_titulo") or 
                              src.get("disciplina_nome") or 
                              src.get("prof_nome") or 
                              src.get("curso_nome") or
                              "Fonte Desconhecida")
                    
                    # Se tiver link, mostra também
                    link = src.get("link") or src.get("prof_lattes")
                    extra = f" ({link})" if link else ""
                    
                    print(f"- {titulo}{extra}")
            
            print("-" * 50)

        except KeyboardInterrupt:
            print("\nEncerrando...")
            break
        except Exception as e:
            print(f"{RED}Erro inesperado no loop principal: {e}{RESET}")

if __name__ == "__main__":
    main()