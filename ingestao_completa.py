import os
import re
from pymongo import MongoClient
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
MONGO_URI = "mongodb+srv://eduardolopesvalerio_db_user:mzTpqZkIMOQ7B1tr@cluster0.knffqsm.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['chatbot_facom']

# Inicializa Modelo de Vetorização (Gratuito/Local)
print("Carregando modelo de IA...")
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# --- 2. FUNÇÕES PARA DADOS ESTRUTURADOS (Cursos, Profs, Disciplinas) ---

def inserir_curso(dados_curso):
    """
    Insere na collection 'cursos' conforme PDF.
    Não há vetorização especificada para esta coleção.
    """
    collection = db['cursos']
    
    # Validação básica dos campos obrigatórios [cite: 5-10]
    required_keys = ["curso_nome", "Curso_sigla", "curso_desc", "curso_duracao", "curso_turno"]
    if not all(k in dados_curso for k in required_keys):
        print(f"ERRO: Dados do curso {dados_curso.get('Curso_sigla')} incompletos.")
        return

    # Evita duplicidade pela sigla
    if collection.find_one({"Curso_sigla": dados_curso["Curso_sigla"]}):
        print(f"Curso {dados_curso['Curso_sigla']} já existe.")
        return

    collection.insert_one(dados_curso)
    print(f"Curso {dados_curso['Curso_sigla']} inserido com sucesso.")


def inserir_disciplina(dados_disciplina):
    """
    Insere na collection 'disciplinas'.
    Regra IA: 'conteudo_semantico' = objetivos + ementa + bibliografia[cite: 32].
    """
    collection = db['disciplinas']

    # 1. Criar Conteúdo Semântico (Concatenação para IA) [cite: 39]
    conteudo_semantico = (
        f"Objetivo: {dados_disciplina.get('disciplina_obj', '')}. "
        f"Ementa: {dados_disciplina.get('disciplina_ementa', '')}. "
        f"Bibliografia: {dados_disciplina.get('disciplina_bibliografia', '')}"
    )

    # 2. Gerar Vetor
    print(f"Vetorizando disciplina: {dados_disciplina.get('disciplina_nome')}...")
    vetor = embedding_model.embed_query(conteudo_semantico)

    # 3. Montar Documento Final
    documento = dados_disciplina.copy()
    documento['conteudo_semantico'] = conteudo_semantico # [cite: 32]
    documento['vector_embedding'] = vetor               # [cite: 33]

    # Inserir
    collection.insert_one(documento)
    print(f"Disciplina {dados_disciplina['disciplina_codigo']} inserida.")


def inserir_professor(dados_prof):
    """
    Insere na collection 'professores'.
    Regra IA: 'conteudo_semantico' = area + pesquisa[cite: 49].
    """
    collection = db['professores']

    # 1. Criar Conteúdo Semântico [cite: 49]
    conteudo_semantico = (
        f"Área: {dados_prof.get('prof_area', '')}. "
        f"Pesquisa: {dados_prof.get('prof_pesquisa', '')}"
    )

    # 2. Gerar Vetor
    print(f"Vetorizando professor: {dados_prof.get('prof_nome')}...")
    vetor = embedding_model.embed_query(conteudo_semantico)

    # 3. Montar Documento
    documento = dados_prof.copy()
    documento['conteudo_semantico'] = conteudo_semantico # [cite: 49]
    documento['vector_embedding'] = vetor               # [cite: 50]

    collection.insert_one(documento)
    print(f"Professor {dados_prof['prof_nome']} inserido.")


# --- 3. FUNÇÕES PARA DADOS NÃO ESTRUTURADOS (PDFs / DocsInst) ---

# Configuração do Splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""]
)

def extrair_metadados_pdf(nome_arquivo):
    """Define metadados automáticos baseado no nome do arquivo"""
    nome_lower = nome_arquivo.lower()
    
    # Lógica de Cursos Alvo [cite: 62]
    cursos = []
    if "bsi" in nome_lower: cursos.append("BSI")
    if "bcc" in nome_lower: cursos.append("BCC")
    if not cursos: cursos.append("TODOS")

    # Lógica de Tipo [cite: 60]
    tipo = "resolucao"
    if "manual" in nome_lower: tipo = "manual"
    elif "edital" in nome_lower: tipo = "edital"

    # Lógica de Ano [cite: 61]
    ano = 2025
    match = re.search(r'202[0-9]', nome_arquivo)
    if match: ano = int(match.group())

    return {"curso_alvo": cursos, "doc_tipo": tipo, "doc_anoVigencia": ano}

def processar_pdf_docsinst(caminho_arquivo):
    """
    Processa PDFs para a collection 'DocsInst'.
    Regra IA: Concatenar título + chunk.
    """
    collection = db['DocsInst']
    nome_arquivo = os.path.basename(caminho_arquivo)
    titulo_doc = nome_arquivo.replace(".pdf", "").replace("_", " ").title()

    # Verifica duplicidade
    if collection.find_one({"doc_titulo": titulo_doc}):
        print(f"PULANDO PDF: {titulo_doc} já existe.")
        return

    print(f"PROCESSANDO PDF: {titulo_doc}...")
    try:
        loader = PyPDFLoader(caminho_arquivo)
        paginas = loader.load()
        chunks = text_splitter.split_documents(paginas)
        
        metadados = extrair_metadados_pdf(nome_arquivo)
        docs_para_inserir = []

        for chunk in chunks:
            conteudo = chunk.page_content
            
            # REGRA ESPECÍFICA DO PDF (Pág 3): Âncora do vetor 
            texto_ancora = f"Documento: {titulo_doc}. Conteúdo: {conteudo}"
            vetor = embedding_model.embed_query(texto_ancora)

            doc_json = {
                "doc_titulo": titulo_doc,           # [cite: 59]
                "doc_tipo": metadados["doc_tipo"],  # [cite: 60]
                "doc_anoVigencia": metadados["doc_anoVigencia"], # [cite: 61]
                "curso_alvo": metadados["curso_alvo"], # [cite: 62]
                "conteudo_chunk": conteudo,         # [cite: 63]
                "pagina_origem": chunk.metadata.get('page', 0) + 1, # [cite: 64]
                "vector_embedding": vetor           # [cite: 65]
            }
            docs_para_inserir.append(doc_json)

        if docs_para_inserir:
            collection.insert_many(docs_para_inserir)
            print(f"PDF {titulo_doc}: {len(docs_para_inserir)} chunks inseridos.")

    except Exception as e:
        print(f"Erro no PDF {nome_arquivo}: {e}")

# --- 4. EXECUÇÃO DE EXEMPLO (MAIN) ---
# Aqui simulamos o uso. Você pode conectar isso a um front-end ou ler de JSONs reais.

if __name__ == "__main__":
    
    # A. Exemplo: Inserir um Curso (Dados da Pág 1)
    curso_exemplo = {
        "curso_nome": "Ciência da Computação", # [cite: 6]
        "Curso_sigla": "BCC",                  # [cite: 7]
        "curso_desc": "Curso focado em fundamentos...", # [cite: 8]
        "curso_duracao": 8,                    # [cite: 9]
        "curso_turno": "Integral"              # [cite: 10]
    }
    inserir_curso(curso_exemplo)

    # B. Exemplo: Inserir uma Disciplina (Dados da Pág 1)
    disciplina_exemplo = {
        "disciplina_nome": "Estruturas de Dados", # [cite: 14]
        "disciplina_codigo": "FACOM123",          # [cite: 15]
        "disciplina_ch": 60,                      # [cite: 16]
        "disciplina_unidAcad": "FACOM",           # [cite: 17]
        "curso": {"curso_sigla": "BCC"},          # [cite: 21]
        "preRequisitos": [{"codigo": "FACOM101", "nome": "Algoritmos"}], # [cite: 25-26]
        "disciplina_obj": "Desenvolver raciocínio algoritmico...",       # [cite: 29]
        "disciplina_ementa": "Listas, pilhas, filas...",                 # [cite: 30]
        "disciplina_bibliografia": "Cormen et al..."                     # [cite: 31]
    }
    inserir_disciplina(disciplina_exemplo)

    # C. Exemplo: Inserir um Professor (Dados da Pág 2)
    prof_exemplo = {
        "prof_nome": "Fulano de Tal",             # [cite: 44]
        "prof_email": "fulano@ufu.br",            # [cite: 45]
        "prof_lattes": "http://lattes.cnpq.br/...", # [cite: 46]
        "prof_area": "Inteligência Artificial",   # [cite: 47]
        "prof_pesquisa": "Sistemas distribuídos e aprendizado profundo" # [cite: 48]
    }
    inserir_professor(prof_exemplo)

    # D. Exemplo: Processar PDFs (Collection DocsInst - Pág 3)
    # Certifique-se de ter a pasta criada
    pasta_pdfs = 'pdfs_facom'
    if os.path.exists(pasta_pdfs):
        arquivos = [f for f in os.listdir(pasta_pdfs) if f.endswith('.pdf')]
        for arq in arquivos:
            processar_pdf_docsinst(os.path.join(pasta_pdfs, arq))
    else:
        print(f"Crie a pasta '{pasta_pdfs}' e coloque PDFs para testar a collection DocsInst.")