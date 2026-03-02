import os
import json
import time
import pdfplumber
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# A NOVA BIBLIOTECA DO GOOGLE
from google import genai
from google.genai import types

# --- 1. CONFIGURAÇÃO INICIAL ---
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['chatbot_facom']

# Coleções
col_disciplinas = db['disciplinas']
col_cursos = db['cursos']
col_professores = db['professores']
col_docs_pai = db['docsInstitucionais']
col_docs_filho = db['docsInstitucionais_chunks'] 

print("⏳ Carregando modelo de Embeddings...")
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Inicializa o cliente novo do Gemini (Ele puxa o GEMINI_API_KEY do .env automaticamente)
gemini_client = genai.Client()

# --- 2. O CORAÇÃO DO SISTEMA: BACKOFF EXPONENCIAL (ATUALIZADO) ---
def chamar_ia_com_protecao(prompt, nome_arquivo):
    """Envia o prompt para o Gemini usando a nova SDK."""
    max_tentativas = 6
    tempo_espera = 15 
    
    for tentativa in range(max_tentativas):
        try:
            # Nova sintaxe da biblioteca google.genai
            resposta = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                )
            )
            return json.loads(resposta.text)
            
        except Exception as e:
            erro_str = str(e).lower()
            if "429" in erro_str or "quota" in erro_str or "exhausted" in erro_str:
                print(f"   ⚠️ Limite do Gemini atingido. Pausando {tempo_espera}s... (Tentativa {tentativa + 1}/{max_tentativas})")
                time.sleep(tempo_espera)
                tempo_espera *= 2 
            else:
                print(f"   ❌ Erro na IA ao processar {nome_arquivo}: {e}")
                return None
    
    print(f"   🚨 Desistindo do arquivo {nome_arquivo} após {max_tentativas} tentativas.")
    return None

def ler_arquivo(caminho):
    """Extrai texto bruto de PDF ou TXT (Essencial para os Professores)"""
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

# --- 3. PROCESSADORES ESPECÍFICOS ---

def processar_disciplina(texto_bruto, nome_arquivo, pasta_origem=""):
    """Extrai e estrutura os dados de Fichas de Disciplinas usando o Gemini."""
    
    # Identifica o curso pela pasta
    sigla_curso = "BCC" if "BCC" in pasta_origem.upper() else "BSI" if "BSI" in pasta_origem.upper() else "Geral"
    
    prompt = f"""
    Você é um assistente de extração de dados acadêmicos da Universidade Federal de Uberlândia (UFU).
    Sua tarefa é ler o texto extraído de um PDF e extrair as informações solicitadas.
    
    Regras de Limpeza:
    1. Corrija erros óbvios de português causados por má leitura de OCR (ex: '<;AO' para 'ÇÃO').
    2. Ignore completamente carimbos, assinaturas, portarias e cabeçalhos inúteis.
    3. Se não encontrar uma informação, retorne null ou 0 (para números).
    4. Para pré-requisitos, retorne apenas uma lista com as siglas (ex: ["GBC024"]). Se não houver, retorne [].

    Extraia para o formato JSON com as exatas chaves abaixo:
    {{
        "codigo": "O código da disciplina. Se não achar, use a sigla extraída do nome do arquivo: {nome_arquivo}",
        "nome": "Nome limpo da disciplina.",
        "carga_horaria": "Apenas o número inteiro. Ex: 60",
        "objetivos": "O texto completo dos objetivos",
        "ementa": "O texto da ementa detalhada, incluindo também os tópicos do Programa se houver.",
        "bibliografia": "A lista de livros da bibliografia",
        "pre_requisitos": ["SIGLA1", "SIGLA2"]
    }}

    Texto bruto do PDF:
    {texto_bruto[:15000]}
    """
    
    dados_limpos = chamar_ia_com_protecao(prompt, nome_arquivo)
    if not dados_limpos: return

    codigo = dados_limpos.get("codigo", "COD_ERRO").upper()
    nome = dados_limpos.get("nome", "Desconhecido")
    
    try:
        carga_horaria = int(dados_limpos.get("carga_horaria", 0) or 0)
    except:
        carga_horaria = 0
        
    objetivos = dados_limpos.get("objetivos", "") or ""
    ementa = dados_limpos.get("ementa", "") or ""
    bibliografia = dados_limpos.get("bibliografia", "") or ""
    lista_siglas_req = dados_limpos.get("pre_requisitos", []) or []

    # Lógica de Pré-requisitos
    lista_pre_reqs = []
    for cod_req in lista_siglas_req:
        disciplina_existente = col_disciplinas.find_one({"disciplina_codigo": cod_req})
        lista_pre_reqs.append({
            "disciplina_id": disciplina_existente["_id"] if disciplina_existente else None,
            "codigo": cod_req,
            "nome": disciplina_existente.get("disciplina_nome", "Desconhecido") if disciplina_existente else "Ainda não cadastrada"
        })

    # Lógica do Curso
    curso_existente = col_cursos.find_one({"Curso_sigla": sigla_curso})
    if curso_existente:
        id_curso_final = curso_existente["_id"]
    else:
        novo_curso = {
            "Curso_sigla": sigla_curso,
            "nome": "Ciência da Computação" if sigla_curso == "BCC" else "Sistemas de Informação" if sigla_curso == "BSI" else "Outro"
        }
        id_curso_final = col_cursos.insert_one(novo_curso).inserted_id

    # Vetor Semântico
    conteudo_semantico = f"Objetivos: {objetivos}\nEmenta Detalhada: {ementa}\nBibliografia: {bibliografia[:500]}...".strip()
    print(f"   ↳ Estruturado: {codigo} | {carga_horaria}h | {nome[:30]}...")
    vetor = embedding_model.embed_query(conteudo_semantico)

    documento_mongo = {
        "disciplina_nome": nome,
        "disciplina_codigo": codigo,
        "disciplina_ch": carga_horaria,
        "disciplina_unidAcad": "FACOM",
        "curso": {"curso_id": id_curso_final, "curso_sigla": sigla_curso},
        "preRequisitos": lista_pre_reqs,
        "disciplina_obj": objetivos,
        "disciplina_ementa": ementa,
        "disciplina_bibliografia": bibliografia,
        "conteudo_semantico": conteudo_semantico,
        "vector_embedding": vetor
    }

    col_disciplinas.replace_one({"disciplina_codigo": codigo}, documento_mongo, upsert=True)
    print("   ✅ Salvo no Mongo com Sucesso!")

def processar_professor(texto_bruto, nome_arquivo):
    """Extrai dados de currículos ou perfis de professores."""
    prompt = f"""
Extraia as informações deste perfil acadêmico e retorne APENAS um JSON (SEM EXPLICAÇÕES ADICIONAIS):
{{
    "nome": "Nome completo do professor",
    "email": "Email institucional (se houver)",
    "lattes": "Link do Lattes (se houver)",
    "area_atuacao": "Área principal de atuação",
    "linhas_pesquisa": "Resumo das linhas de pesquisa"
}}
Caso não encontre alguma informação, apenas deixe vazio ou null.
Texto: {texto_bruto[:15000]}
    """
    dados = chamar_ia_com_protecao(prompt, nome_arquivo)
    if not dados: return
    
    conteudo_concatenado = f"Área de Atuação: {dados.get('area_atuacao', '')}. Linhas de Pesquisa: {dados.get('linhas_pesquisa', '')}."
    vetor = embedding_model.embed_query(conteudo_concatenado)
    
    doc = {
        "prof_nome": dados.get("nome", "Desconhecido"),
        "prof_email": dados.get("email", ""),
        "prof_lattes": dados.get("lattes", ""),
        "prof_pesquisa": dados.get("linhas_pesquisa", ""),
        "prof_area": dados.get("area_atuacao", ""),
        "conteudo_concatenado": conteudo_concatenado,
        "vetor_unificado": vetor
    }
    col_professores.replace_one({"prof_nome": doc["prof_nome"]}, doc, upsert=True)
    print(f"   ✅ Professor {doc['prof_nome']} salvo!")

def processar_institucional(texto_bruto, nome_arquivo):
    """Implementa o Parent-Child Indexing para PDFs longos."""
    prompt = f"""
    Analise a introdução deste documento institucional e retorne um JSON (SEM TEXTO EXTRA):
    {{
        "titulo": "Título oficial do documento",
        "descricao": "Um resumo de 2 linhas sobre o que é este documento"
    }}
    Texto: {texto_bruto[:5000]}
    """
    metadados = chamar_ia_com_protecao(prompt, nome_arquivo)
    if not metadados: return

    doc_pai = {
        "doc_nome": metadados.get("titulo", nome_arquivo),
        "doc_descricao": metadados.get("descricao", ""),
        "texto_completo": texto_bruto, 
        "arquivo_origem": nome_arquivo
    }
    parent_id = col_docs_pai.insert_one(doc_pai).inserted_id
    
    print(f"   ✂️ Fatiando documento pai '{doc_pai['doc_nome']}'...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(texto_bruto)
    
    chunks_mongo = []
    for i, chunk in enumerate(chunks):
        vetor = embedding_model.embed_query(chunk)
        chunks_mongo.append({
            "parent_id": parent_id,
            "chunk_indice": i,
            "conteudo_texto": chunk,
            "vetor_chunk": vetor
        })
    
    if chunks_mongo:
        col_docs_filho.insert_many(chunks_mongo)
    
    print(f"   ✅ Documento Institucional salvo com {len(chunks)} pedaços!")

# --- 4. O MAESTRO (LOOP PRINCIPAL) ---
if __name__ == "__main__":
    print("🚀 INICIANDO PIPELINE DE INGESTÃO UNIFICADA...")
    
    # Mapeamento: Pasta -> Função que sabe processar aquela pasta
    # Assumindo que você tem essas pastas dentro do seu projeto
    pastas_alvo = {
        "pdfs_fichas_facom/BCC": processar_disciplina,
        "pdfs_fichas_facom/BSI": processar_disciplina,
        "pdfs_fichas_facom/professores": processar_professor,
        "pdfs_fichas_facom/institucionais": processar_institucional
    }
    
    for pasta, funcao_processadora in pastas_alvo.items():
        if not os.path.exists(pasta):
            print(f"⚠️ Pasta não encontrada: {pasta}. Pulando...")
            continue
            
        print(f"\n📂 Lendo diretório: {pasta}")
        arquivos = os.listdir(pasta)
        
        for arq in arquivos:
            # ---> A CORREÇÃO DE OURO: Agora aceitamos os PDFs das disciplinas E os TXTs dos professores
            if not (arq.lower().endswith('.pdf') or arq.lower().endswith('.txt')): 
                continue
            
            caminho = os.path.join(pasta, arq)
            print(f"\n📄 Lendo: {arq}")
            texto = ler_arquivo(caminho)
            
            if texto:
                # Se for disciplina, passamos a pasta junto para ele saber se é BCC ou BSI
                if funcao_processadora == processar_disciplina:
                    funcao_processadora(texto, arq, pasta)
                else:
                    funcao_processadora(texto, arq)
                    
            # Respiro para não estourar tokens
            time.sleep(3) 

    print("\n🎉 Processo de Ingestão Concluído!")