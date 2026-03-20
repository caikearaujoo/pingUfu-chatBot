import os
import sys
import json
from dotenv import load_dotenv

# --- Imports do FastAPI ---
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Carrega variáveis do arquivo .env
load_dotenv()

print(f"DEBUG MONGO: {os.getenv('MONGO_URI')}")

# Adiciona a raiz ao path para garantir os imports (fundamental para achar a pasta 'rag')
sys.path.append(os.path.dirname(__file__))

from rag.router import route_question

# --- 1. Cliente GEMINI ---
class GeminiClient:
    def __init__(self):
        try:
            from google import genai
            from google.genai import types
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY não encontrada no .env")
            
            self.client = genai.Client()
            self.types = types
            
        except ImportError:
            print("Erro: Biblioteca 'google-genai' não instalada.")
            sys.exit(1)
        except ValueError as e:
            print(f"Erro: {e}")
            sys.exit(1)

    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        try:
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

# --- 2. Cliente MOCK ---
class MockClient:
    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        if "Classifique" in prompt:
            if "estágio" in prompt: return json.dumps({"categoria": "INSTITUCIONAL", "curso_alvo": "BCC"})
            if "aprende" in prompt: return json.dumps({"categoria": "SEMANTICA_DISCIPLINA"})
            if "pré-requisito" in prompt: return json.dumps({"categoria": "ESTRUTURAL_DISCIPLINA"})
            if "pesquisa" in prompt: return json.dumps({"categoria": "SEMANTICA_PROFESSOR"})
            return json.dumps({"categoria": "MISTA"})
        
        return "🤖 [RESPOSTA MOCK]\nO sistema está rodando em modo de teste."

# --- CONFIGURAÇÃO DA API ---
USE_MOCK = False  
ia_client = MockClient() if USE_MOCK else GeminiClient()

app = FastAPI(title="PingUfu API", description="Backend Web para o Chatbot da FACOM")

# Configuração essencial para o frontend (React/Vite) conseguir conversar com a API
app.add_middleware(
    CORSMiddleware,
    # Liberando as portas específicas do Vite e um curinga geral por segurança
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS DE DADOS (Contratos entre o Front e o Back) ---
class FonteResponse(BaseModel):
    titulo: str
    link: Optional[str] = None

class ChatRequest(BaseModel):
    pergunta: str
    chat_id: Optional[str] = None 

class ChatResponse(BaseModel):
    resposta_ia: str
    fontes: List[FonteResponse]
    chat_id: Optional[str] = None

# --- ROTAS DA API ---

@app.get("/")
def home():
    return {"status": "PingUfu API rodando! 🚀 Acesse /docs para testar."}

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        # Chama a mágica do seu RAG
        response_data = route_question(request.pergunta, ia_client)
        
        # 1. TRAVA DE SEGURANÇA: Se o RAG retornar só um texto (ex: mensagem de erro)
        if isinstance(response_data, str):
            return ChatResponse(
                resposta_ia=response_data,
                fontes=[],
                chat_id=request.chat_id
            )
        
        fontes_formatadas = []
        
        # 2. EXTRAÇÃO DE FONTES: Se o RAG retornou o dicionário corretamente
        if isinstance(response_data, dict) and response_data.get("sources"):
            for src in response_data["sources"]:
                titulo = (src.get("doc_nome") or 
                          src.get("doc_titulo") or
                          src.get("disciplina_nome") or 
                          src.get("prof_nome") or 
                          src.get("curso_nome") or
                          "Fonte Institucional FACOM")
                
                link = src.get("link") or src.get("prof_lattes")
                
                fontes_formatadas.append(FonteResponse(titulo=titulo, link=link))

        # 3. RETORNO FINAL PARA O REACT
        return ChatResponse(
            resposta_ia=response_data.get("answer", "Desculpe, não consegui formular a resposta."),
            fontes=fontes_formatadas,
            chat_id=request.chat_id
        )

    except Exception as e:
        print(f"Erro capturado no endpoint: {e}") # Aparece no terminal para você debugar
        raise HTTPException(status_code=500, detail=f"Erro interno no motor do PingUfu: {str(e)}")