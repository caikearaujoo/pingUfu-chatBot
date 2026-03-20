#!/usr/bin/env python3
"""
Script de Diagnóstico para o Chatbot PingUFU
Testa cada componente do sistema para identificar problemas
"""

import os
import sys
import json
from dotenv import load_dotenv

# Cores para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(title):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"{title}")
    print(f"{'='*60}{Colors.RESET}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

# === TESTE 1: Variáveis de Ambiente ===
def test_env_variables():
    print_header("TESTE 1: Variáveis de Ambiente")

    load_dotenv()

    mongo_uri = os.getenv("MONGO_URI")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if mongo_uri:
        print_success(f"MONGO_URI encontrada (primeiros 50 chars): {mongo_uri[:50]}...")
    else:
        print_error("MONGO_URI não encontrada no .env")
        return False

    if gemini_key:
        print_success(f"GEMINI_API_KEY encontrada (primeiros 20 chars): {gemini_key[:20]}...")
    else:
        print_error("GEMINI_API_KEY não encontrada no .env")
        return False

    return True

# === TESTE 2: Conexão MongoDB ===
def test_mongodb_connection():
    print_header("TESTE 2: Conexão MongoDB")

    try:
        import certifi
        from pymongo import MongoClient

        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            print_error("MONGO_URI não definida")
            return False

        print_info("Tentando conectar ao MongoDB...")
        client = MongoClient(
            mongo_uri,
            tlsCAFile=certifi.where(),
            tls=True,
            retryWrites=False,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000
        )

        # Tenta fazer ping
        client.admin.command('ping')
        print_success("MongoDB conectado com sucesso!")

        # Verifica database
        db = client["chatbot_facom"]
        print_success(f"Database 'chatbot_facom' acessível")

        # Verifica collections
        collections = db.list_collection_names()
        print_info(f"Collections encontradas: {', '.join(collections)}")

        # Conta documentos em cada collection
        print_info("\nContagem de documentos por collection:")
        for col_name in ["disciplinas", "professores", "docsInstitucionais", "docsInstitucionais_chunks"]:
            if col_name in collections:
                count = db[col_name].count_documents({})
                if count > 0:
                    print_success(f"  {col_name}: {count} documentos")
                else:
                    print_error(f"  {col_name}: VAZIA!")
            else:
                print_error(f"  {col_name}: NÃO ENCONTRADA!")

        # Verifica índices
        print_info("\nÍndices de Vector Search:")
        try:
            indexes = db["disciplinas"].list_search_indexes()
            indexes_list = list(indexes)
            if indexes_list:
                for idx in indexes_list:
                    print_success(f"  Índice encontrado: {idx.get('name')}")
            else:
                print_error("  Nenhum índice de busca encontrado!")
        except Exception as e:
            print_warning(f"  Não foi possível listar índices: {e}")

        client.close()
        return True

    except Exception as e:
        print_error(f"Falha na conexão: {str(e)}")
        return False

# === TESTE 3: Gemini API ===
def test_gemini_api():
    print_header("TESTE 3: Gemini API")

    try:
        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print_error("GEMINI_API_KEY não definida")
            return False

        print_info("Tentando inicializar Cliente Gemini...")
        client = genai.Client()
        print_success("Cliente Gemini inicializado")

        # Tenta fazer uma chamada simples
        print_info("Tentando fazer uma chamada de teste...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Responda com uma única palavra: OK",
            config=types.GenerateContentConfig(temperature=0.0)
        )

        if response.text:
            print_success(f"Resposta recebida: {response.text[:50]}...")
            return True
        else:
            print_error("Resposta vazia do Gemini")
            return False

    except Exception as e:
        print_error(f"Falha na Gemini API: {str(e)}")
        return False

# === TESTE 4: Embeddings ===
def test_embeddings():
    print_header("TESTE 4: Geração de Embeddings")

    try:
        print_info("Carregando modelo de embeddings...")
        from rag.embeddings import embed_text

        test_text = "Estruturas de Dados"
        print_info(f"Gerando embedding para: '{test_text}'...")

        embedding = embed_text(test_text)

        if isinstance(embedding, list) and len(embedding) > 0:
            print_success(f"Embedding gerado com sucesso!")
            print_info(f"Dimensões: {len(embedding)}")
            print_info(f"Primeiros 5 valores: {embedding[:5]}")
            return True
        else:
            print_error("Embedding inválido ou vazio")
            return False

    except Exception as e:
        print_error(f"Falha ao gerar embedding: {str(e)}")
        return False

# === TESTE 5: Classificador ===
def test_classifier():
    print_header("TESTE 5: Classificador de Perguntas")

    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from rag.classifier import classify_question
        from main import ia_client

        test_question = "Quais são os pré-requisitos de Estruturas de Dados?"
        print_info(f"Classificando pergunta: '{test_question}'...")

        result = classify_question(test_question, ia_client)

        if isinstance(result, dict) and "categoria" in result:
            categoria = result.get("categoria")
            print_success(f"Pergunta classificada como: {categoria}")
            print_info(f"Resultado completo: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print_error(f"Resultado inválido: {result}")
            return False

    except Exception as e:
        print_error(f"Falha no classificador: {str(e)}")
        return False

# === TESTE 6: Handlers de Retrieval ===
def test_retrieval():
    print_header("TESTE 6: Retrieval de Dados (Busca no MongoDB)")

    try:
        sys.path.insert(0, os.path.dirname(__file__))

        print_info("Testando busca de disciplinas...")
        from rag.retrieval.disciplinas_semantica import search_disciplina_semantica

        results = search_disciplina_semantica("Estruturas de Dados", top_k=1)
        if results:
            print_success(f"Busca de disciplinas retornou {len(results)} resultado(s)")
            print_info(f"Primeiro resultado: {list(results[0].keys())}")
            return True
        else:
            print_error("Busca de disciplinas retornou vazio")
            return False

    except Exception as e:
        print_error(f"Falha no retrieval: {str(e)}")
        return False

# === TESTE 7: Router Completo ===
def test_router():
    print_header("TESTE 7: Router Completo (Fluxo Ponta-a-Ponta)")

    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from rag.router import route_question
        from main import ia_client

        test_question = "O que aprendo em Engenharia de Software?"
        print_info(f"Processando pergunta: '{test_question}'...")

        result = route_question(test_question, ia_client)

        if isinstance(result, dict) and "answer" in result:
            print_success("Router processou a pergunta com sucesso!")
            print_info(f"Resposta: {result['answer'][:100]}...")
            print_info(f"Fontes encontradas: {len(result.get('sources', []))}")
            return True
        else:
            print_error(f"Resultado inválido do router: {result}")
            return False

    except Exception as e:
        print_error(f"Falha no router: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# === MAIN ===
def main():
    print(f"\n{Colors.BLUE}🔍 INICIANDO DIAGNÓSTICO DO CHATBOT PINGUFU{Colors.RESET}")

    results = {}

    results["env_variables"] = test_env_variables()
    results["mongodb"] = test_mongodb_connection()
    results["gemini"] = test_gemini_api()
    results["embeddings"] = test_embeddings()
    results["classifier"] = test_classifier()
    results["retrieval"] = test_retrieval()
    results["router"] = test_router()

    # === RESUMO ===
    print_header("RESUMO DO DIAGNÓSTICO")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nResultados: {passed}/{total} testes passaram\n")

    for test_name, passed in results.items():
        status = f"{Colors.GREEN}PASSOU{Colors.RESET}" if passed else f"{Colors.RED}FALHOU{Colors.RESET}"
        print(f"  {test_name.upper():25} {status}")

    print(f"\n{Colors.YELLOW}Recomendações:{Colors.RESET}")

    if not results["env_variables"]:
        print("  1. Verificar se o arquivo .env está correto")

    if not results["mongodb"]:
        print("  2. Verificar credenciais do MongoDB Atlas")
        print("     - IP está whitelisted?")
        print("     - Credenciais estão corretas?")

    if not results["gemini"]:
        print("  3. Verificar GEMINI_API_KEY no Google Cloud")

    if not results["embeddings"]:
        print("  4. Verificar instalação do sentence-transformers")
        print("     pip install sentence-transformers")

    if not results["classifier"]:
        print("  5. Gemini API pode estar inativa ou cota atingida")

    if not results["retrieval"]:
        print("  6. Verificar se MongoDB tem dados e índices criados")

    if not results["router"]:
        print("  7. Fluxo completo falhou - ver log acima")

    print()

if __name__ == "__main__":
    main()
