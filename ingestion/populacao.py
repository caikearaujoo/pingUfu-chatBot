import os
import json
import time
import pdfplumber
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# BIBLIOTECA DO GOOGLE GENAI
from google import genai
from google.genai import types

# --- 1. CONFIGURAÇÃO INICIAL ---
load_dotenv()

# Caminhos automáticos para encontrar os PDFs
# Pega a pasta onde este arquivo está (ingestion)
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
# Sobe para 'pingUfu-chatBot' -> Sobe para 'PingUFU' (raiz do projeto)
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))

MONGO_URI = os.getenv("MONGO_URI")
# Conexão com certifi para evitar erro de SSL
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['chatbot_facom']

# Coleções
col_disciplinas = db['disciplinas']
col_cursos = db['cursos']
col_professores = db['professores']
col_docs_pai = db['docsInstitucionais']
col_docs_filho = db['docsInstitucionais_chunks']

print("⏳ Carregando modelo de Embeddings...")
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Inicializa o Gemini
gemini_client = genai.Client()

# --- 2. FUNÇÕES DE APOIO ---

def chamar_ia_com_protecao(prompt, nome_arquivo):
    """Envia o prompt para o Gemini com retry (Backoff Exponencial)."""
    max_tentativas = 6
    tempo_espera = 15
    for tentativa in range(max_tentativas):
        try:
            resposta = gemini_client.models.generate_content(
                model='gemini-2.0-flash', # Atualizado para a versão estável mais comum
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                )
            )
            return json.loads(resposta.text)
        except Exception as e:
            erro_str = str(e).lower()
            if "429" in erro_str or "quota" in erro_str:
                print(f"⚠️ Limite Gemini. Pausando {tempo_espera}s... (Tentativa {tentativa + 1})")
                time.sleep(tempo_espera)
                tempo_espera *= 2
            else:
                print(f"❌ Erro na IA ({nome_arquivo}): {e}")
                return None
    return None

def ler_arquivo(caminho):
    """Extrai texto de PDF ou TXT."""
    texto = ""
    extensao = caminho.lower().split('.')[-1]
    try:
        if extensao == 'pdf':
            with pdfplumber.open(caminho) as pdf:
                for page in pdf.pages:
                    texto += page.extract_text() + "\n"
        elif extensao == 'txt':
            with open(caminho, 'r', encoding='utf-8') as f:
                texto = f.read()
    except Exception as e:
        print(f"Erro ao ler arquivo {caminho}: {e}")
    return texto

# --- 3. PROCESSADORES ---

def processar_disciplina(texto_bruto, nome_arquivo, pasta_origem=""):
    sigla_curso = "BCC" if "BCC" in pasta_origem.upper() else "BSI" if "BSI" in pasta_origem.upper() else "Geral"
    
    prompt = f"""
    Extraia os dados desta disciplina da UFU para JSON:
    {{
        "codigo": "Código da disciplina",
        "nome": "Nome da disciplina",
        "carga_horaria": 60,
        "objetivos": "Texto objetivos",
        "ementa": "Texto ementa",
        "bibliografia": "Texto bibliografia",
        "pre_requisitos": ["SIGLA1"]
    }}
    Texto: {texto_bruto[:15000]}
    """
    dados = chamar_ia_com_protecao(prompt, nome_arquivo)
    if not dados: return

    # Lógica de curso e pre-requisitos (Simplificada para o exemplo)
    curso_existente = col_cursos.find_one({"Curso_sigla": sigla_curso})
    id_curso = curso_existente["_id"] if curso_existente else col_cursos.insert_one({"Curso_sigla": sigla_curso}).inserted_id

    conteudo_semantico = f"Objetivos: {dados.get('objetivos')}\nEmenta: {dados.get('ementa')}"
    vetor = embedding_model.embed_query(conteudo_semantico)

    doc = {
        "disciplina_nome": dados.get("nome"),
        "disciplina_codigo": dados.get("codigo", nome_arquivo).upper(),
        "disciplina_ch": dados.get("carga_horaria"),
        "curso": {"curso_id": id_curso, "curso_sigla": sigla_curso},
        "disciplina_ementa": dados.get("ementa"),
        "vector_embedding": vetor
    }
    col_disciplinas.replace_one({"disciplina_codigo": doc["disciplina_codigo"]}, doc, upsert=True)
    print(f"   ✅ Disciplina {doc['disciplina_codigo']} salva!")

def processar_professor(texto_bruto, nome_arquivo):
    prompt = f"Extraia nome, email, lattes, area_atuacao e linhas_pesquisa para JSON deste texto: {texto_bruto[:15000]}"
    dados = chamar_ia_com_protecao(prompt, nome_arquivo)
    if not dados: return

    conteudo = f"{dados.get('area_atuacao')}. {dados.get('linhas_pesquisa')}"
    vetor = embedding_model.embed_query(conteudo)

    doc = {
        "prof_nome": dados.get("nome"),
        "prof_area": dados.get("area_atuacao"),
        "vetor_unificado": vetor
    }
    col_professores.replace_one({"prof_nome": doc["prof_nome"]}, doc, upsert=True)
    print(f"   ✅ Professor {doc['prof_nome']} salvo!")

def processar_institucional(texto_bruto, nome_arquivo):
    # Lógica de Parent-Child fatiando o texto
    doc_pai = {"doc_nome": nome_arquivo, "texto_completo": texto_bruto}
    parent_id = col_docs_pai.insert_one(doc_pai).inserted_id

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(texto_bruto)

    for i, chunk in enumerate(chunks):
        vetor = embedding_model.embed_query(chunk)
        col_docs_filho.insert_one({
            "parent_id": parent_id,
            "conteudo_texto": chunk,
            "vetor_chunk": vetor
        })
    print(f"   ✅ Doc Institucional {nome_arquivo} fatiado e salvo!")

# --- 4. MAPA DE PASTAS (Definido após as funções) ---

pastas_alvo = {
    os.path.join(ROOT_DIR, "pdfs_fichas_facom", "BCC"): processar_disciplina,
    os.path.join(ROOT_DIR, "pdfs_fichas_facom", "BSI"): processar_disciplina,
    os.path.join(ROOT_DIR, "pdfs_fichas_facom", "professores"): processar_professor,
    os.path.join(ROOT_DIR, "pdfs_fichas_facom", "institucionais"): processar_institucional
}

# --- 5. EXECUÇÃO ---

if __name__ == "__main__":
    print(f"🚀 INICIANDO INGESTÃO... (Buscando em: {ROOT_DIR})")
    
    for pasta, funcao in pastas_alvo.items():
        if not os.path.exists(pasta):
            print(f"⚠️ Pasta não encontrada: {pasta}")
            continue
            
        print(f"\n📂 Processando: {pasta}")
        for arq in os.listdir(pasta):
            if arq.lower().endswith(('.pdf', '.txt')):
                caminho = os.path.join(pasta, arq)
                texto = ler_arquivo(caminho)
                if texto:
                    if funcao == processar_disciplina:
                        funcao(texto, arq, pasta)
                    else:
                        funcao(texto, arq)
                time.sleep(2)

    print("\n🎉 Processo Concluído!")