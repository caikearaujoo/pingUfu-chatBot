import os
import re
import sys
from pymongo import MongoClient
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

# --- 1. CONFIGURAÇÃO ---
load_dotenv() 

MONGO_URI = os.getenv("MONGO_URI") 
if not MONGO_URI:
    print("Erro: MONGO_URI não definido no .env")
    sys.exit(1)

client = MongoClient(MONGO_URI)
db = client['chatbot_facom']

print("Carregando modelo de Embeddings...")
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# --- 2. FUNÇÕES AUXILIARES ---

def extrair_metadados_pdf(nome_arquivo):
    nome_lower = nome_arquivo.lower()
    cursos = []
    if "bsi" in nome_lower: cursos.append("BSI")
    if "bcc" in nome_lower: cursos.append("BCC")
    if not cursos: cursos.append("TODOS")
    
    tipo = "resolucao"
    if "manual" in nome_lower: tipo = "manual"
    elif "edital" in nome_lower: tipo = "edital"
    elif "projeto" in nome_lower and "pedagogico" in nome_lower: tipo = "ppc"

    ano = 2025
    match = re.search(r'202[0-9]', nome_arquivo)
    if match: ano = int(match.group())

    return {"curso_alvo": cursos, "doc_tipo": tipo, "doc_anoVigencia": ano}

def criar_chunk_pai(titulo_doc, texto, metadados):
    texto_ancora = f"{titulo_doc}. {texto[:1000]}" 
    return {
        "doc_titulo": titulo_doc,
        "conteudo_completo": texto,
        "vector_embedding": embedding_model.embed_query(texto_ancora),
        "metadados": metadados
    }

def criar_chunks_filhos(texto, parent_id):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    partes = splitter.split_text(texto)
    filhos = []
    for parte in partes:
        filhos.append({
            "parent_id": parent_id,
            "conteudo_chunk": parte,
            "vector_embedding": embedding_model.embed_query(parte)
        })
    return filhos

# --- FUNÇÃO PRINCIPAL INTELIGENTE ---
def processar_pdf_inteligente(caminho_arquivo):
    nome_arquivo = os.path.basename(caminho_arquivo)
    nome_lower = nome_arquivo.lower()
    
    try:
        loader = PyPDFLoader(caminho_arquivo)
        paginas = loader.load()
        texto_completo = "\n".join(p.page_content for p in paginas)
    except Exception as e:
        print(f"❌ Erro ao ler {nome_arquivo}: {e}")
        return

    # --- ESTRATÉGIA 1: PROFESSOR (Ex: andre-ricardo-backes-2022_1.pdf) ---
    # Procura padrão: nome-sobrenome-ano_semestre.pdf (ignora palavras reservadas como 'projeto', 'edital')
    palavras_reservadas = ["projeto", "edital", "manual", "horario", "resolucao", "facom", "gsi", "bcc"]
    eh_reservado = any(p in nome_lower for p in palavras_reservadas)
    
    # Regex: letras e hifens, seguido de ano_semestre (ex: -2022_1)
    match_prof = re.match(r'([a-z-]+)-(\d{4}_\d)\.pdf', nome_lower)

    if match_prof and not eh_reservado:
        nome_slug = match_prof.group(1)
        nome_real = nome_slug.replace("-", " ").title()
        
        print(f"👨‍🏫 Detectei PROFESSOR: {nome_real}")
        
        doc_prof = {
            "prof_nome": nome_real,
            "prof_area": "Extraído do Plano de Trabalho", # Poderíamos tentar extrair do texto com regex, mas ok
            "prof_email": "Não disponível no nome do arquivo",
            "conteudo": texto_completo, # O PDF inteiro vira contexto
            "vector_embedding": embedding_model.embed_query(f"Professor {nome_real}. {texto_completo[:1000]}")
        }
        
        # Upsert (Atualiza se existir, cria se não)
        db['professores'].replace_one(
            {"prof_nome": nome_real}, 
            doc_prof, 
            upsert=True
        )
        return

    # --- ESTRATÉGIA 2: DISCIPLINA (Ex: gsi520-banco-de-dados.pdf) ---
    match_disciplina = re.match(r'([a-z]{3,5}\d{3,5})[_-](.+)\.pdf', nome_lower)
    
    if match_disciplina:
        codigo = match_disciplina.group(1).upper() 
        nome_bruto = match_disciplina.group(2).replace("_", " ").replace("-", " ").title() 
        
        print(f"📚 Detectei DISCIPLINA: {codigo} - {nome_bruto}")
        
        doc_disciplina = {
            "disciplina_codigo": codigo,
            "disciplina_nome": nome_bruto,
            "disciplina_obj": "Extraído do PDF",
            "disciplina_ementa": texto_completo[:1000],
            "conteudo": texto_completo,
            "vector_embedding": embedding_model.embed_query(f"Disciplina {codigo} {nome_bruto}. {texto_completo[:500]}")
        }
        
        db['disciplinas'].replace_one(
            {"disciplina_codigo": codigo}, 
            doc_disciplina, 
            upsert=True
        )
        return 

    # --- ESTRATÉGIA 3: CURSO (PPC) (Ex: projeto_pedagogico_bsi...) ---
    if "projeto" in nome_lower and "pedagogico" in nome_lower:
        sigla = "BSI" if "bsi" in nome_lower else "BCC" if "bcc" in nome_lower else "OUTRO"
        nome_curso = "Sistemas de Informação" if sigla == "BSI" else "Ciência da Computação"
        
        print(f"🎓 Detectei CURSO (PPC): {sigla} - {nome_curso}")
        
        doc_curso = {
            "Curso_sigla": sigla,
            "curso_nome": nome_curso,
            "curso_desc": "Projeto Pedagógico do Curso (PPC) extraído de PDF.",
            "conteudo_completo": texto_completo, # PPCs são grandes, isso ajuda o RAG
            "vector_embedding": embedding_model.embed_query(f"Curso {nome_curso} {sigla}. {texto_completo[:1000]}")
        }

        db['cursos'].replace_one(
            {"Curso_sigla": sigla},
            doc_curso,
            upsert=True
        )
        # Nota: PPCs também são documentos institucionais importantes, 
        # então deixamos "cair" para a Estratégia 4 também (sem return aqui) para ter busca por capítulos.

    # --- ESTRATÉGIA 4: GENÉRICO (Manuais, Editais, PPCs indexados por capítulo) ---
    
    collection_pai = db["documentos_pai"]
    collection_filho = db["documentos_filhos"]
    titulo_doc = nome_arquivo.replace(".pdf", "").replace("_", " ").title()

    if collection_pai.find_one({"doc_titulo": titulo_doc}):
        print(f"⏭️  PULANDO GERAL: {titulo_doc} (Já existe).")
        return

    print(f"📄 PROCESSANDO DOC GERAL: {titulo_doc}")
    
    metadados = extrair_metadados_pdf(nome_arquivo)
    
    pai = criar_chunk_pai(titulo_doc, texto_completo, metadados)
    parent_id = collection_pai.insert_one(pai).inserted_id

    filhos = criar_chunks_filhos(texto_completo, parent_id)
    if filhos:
        collection_filho.insert_many(filhos)

# --- 3. EXECUÇÃO ---

if __name__ == "__main__":
    print("--- INICIANDO INGESTÃO INTELIGENTE 2.0 ---")
    
    pasta_pdfs = 'pdfs_facom' 

    if os.path.exists(pasta_pdfs):
        arquivos = [f for f in os.listdir(pasta_pdfs) if f.endswith('.pdf')]
        print(f"Encontrados {len(arquivos)} PDFs na pasta '{pasta_pdfs}'.")
        
        for arq in arquivos:
            caminho = os.path.join(pasta_pdfs, arq)
            processar_pdf_inteligente(caminho)
            
        print("✅ Ingestão concluída!")
    else:
        print(f"⚠️  Pasta '{pasta_pdfs}' não encontrada.")