#!/usr/bin/env python3
"""
Script Rápido de Teste SSL/TLS MongoDB
Verifica se a conexão está funcionando com as novas configurações
"""

import os
import sys
from dotenv import load_dotenv

# Cores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

load_dotenv()

print(f"\n{YELLOW}🔧 Testando Conexão SSL/TLS MongoDB...{RESET}\n")

# 1. Verificar variáveis
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    print(f"{RED}❌ MONGO_URI não definida em .env{RESET}\n")
    sys.exit(1)

print(f"{GREEN}✅ MONGO_URI encontrada{RESET}")

# 2. Tentar conectar
try:
    import certifi
    from pymongo import MongoClient

    print(f"\n{YELLOW}Tentando conectar...{RESET}")

    client = MongoClient(
        mongo_uri,
        tlsCAFile=certifi.where(),
        tls=True,
        retryWrites=False,
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000
    )

    # Fazer ping
    client.admin.command('ping')
    print(f"{GREEN}✅ MongoDB conectado!{RESET}")

    # Verificar database
    db = client["chatbot_facom"]
    print(f"{GREEN}✅ Database 'chatbot_facom' acessível{RESET}")

    # Listar collections
    collections = db.list_collection_names()
    print(f"{GREEN}✅ Collections encontradas: {', '.join(collections)}{RESET}")

    print(f"\n{GREEN}🎉 CONEXÃO FUNCIONANDO!{RESET}\n")

except Exception as e:
    print(f"\n{RED}❌ ERRO NA CONEXÃO:{RESET}")
    print(f"{RED}{str(e)}{RESET}\n")

    # Diagnóstico
    error_str = str(e).lower()

    if "ssl" in error_str or "tls" in error_str:
        print(f"{YELLOW}💡 Parece ser problema de SSL/TLS. Tente:{RESET}")
        print(f"   1. pip install --upgrade certifi pyOpenSSL")
        print(f"   2. Sincronizar relógio do sistema")
        print()

    elif "authentication" in error_str or "auth" in error_str:
        print(f"{YELLOW}💡 Parece ser problema de autenticação. Verificar:{RESET}")
        print(f"   1. MONGO_URI está correta?")
        print(f"   2. Credenciais no MongoDB Atlas ainda são válidas?")
        print()

    elif "timeout" in error_str:
        print(f"{YELLOW}💡 Timeout na conexão. Tente:{RESET}")
        print(f"   1. Verificar conexão de internet")
        print(f"   2. Adicionar seu IP em MongoDB Atlas > Network Access")
        print()

    sys.exit(1)
