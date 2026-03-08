import os
import sys
import json
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# Adiciona a raiz ao path para garantir os imports
sys.path.append(os.path.dirname(__file__))

# AGORA SIM! Importando o seu roteador real oficial
from rag.router import route_question

# --- Cores para o Terminal (Deixa o chat bonitão) ---
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

# --- 1. Cliente GEMINI (O Cérebro Gratuito com a SDK Nova) ---
class GeminiClient:
    def __init__(self):
        try:
            from google import genai
            from google.genai import types
            
            # Pegando a chave exata que a gente colocou no .env
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY não encontrada no .env")
            
            # Instancia o cliente novo do Google
            self.client = genai.Client()
            self.types = types
            
        except ImportError:
            print(f"{RED}Erro: Biblioteca 'google-genai' não instalada.{RESET}")
            print("Instale com: pip install google-genai")
            sys.exit(1)
        except ValueError as e:
            print(f"{RED}{e}{RESET}")
            sys.exit(1)

    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        try:
            # Invoca o modelo do jeito novo
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    temperature=temperature
                )
            )
            return response.text
        except Exception as e:
            return f"Erro na API do Google: {str(e)}"

# --- 2. Cliente MOCK (Para quando a internet cair ou acabar a cota rs) ---
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
# Coloquei False pra gente testar o bot de verdade valendo!
USE_MOCK = False  

def main():
    print(f"{BOLD}🎓 pingUfu Bot - FACOM (Powered by Gemini){RESET}")
    print("-------------------------------------------------------")
    
    # Seleção do Cliente
    if USE_MOCK:
        print(f"{YELLOW}⚠️  Rodando em MODO MOCK (Sem IA real){RESET}")
        client = MockClient()
    else:
        print(f"{GREEN}🚀 Rodando em MODO REAL (Conectado ao Google Gemini e MongoDB){RESET}")
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

            print(f"{YELLOW}Processando... (Consultando a base da FACOM){RESET}")
            
            # --- O CORAÇÃO DO SISTEMA ---
            # Aqui a mágica acontece! A pergunta desce pro router e ele faz o corre
            response = route_question(pergunta, client)
            # ---------------------------

            print(f"\n{GREEN}PingUfu Bot:{RESET}")
            print(response["answer"])
            
            if response.get("sources"):
                print(f"\n{BOLD}[Fontes Utilizadas]:{RESET}")
                for src in response["sources"]:
                    # Pegando os nomes certinhos baseados em como a gente salvou no Mongo
                    titulo = (src.get("doc_nome") or 
                              src.get("doc_titulo") or
                              src.get("disciplina_nome") or 
                              src.get("prof_nome") or 
                              src.get("curso_nome") or
                              "Fonte Desconhecida")
                    
                    # Se o professor tiver lattes, mostra o link
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