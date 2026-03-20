#!/usr/bin/env python3
"""
Teste BÁSICO MongoDB - sem nenhuma flag SSL/TLS
Serve para diagnosticar se o problema é TLS ou credenciais
"""

import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")

if not mongo_uri:
    print("❌ MONGO_URI não definida")
    exit(1)

print(f"Testando conexão BÁSICA (sem TLS)...")
print(f"URI: {mongo_uri[:60]}...\n")

try:
    from pymongo import MongoClient

    # Teste 1: Conexão mais simples possível
    print("Teste 1: Conexão simples (sem flags)...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ Funcionou sem TLS!\n")

except Exception as e:
    error_str = str(e)
    print(f"❌ Erro: {error_str[:200]}\n")

    if "SSL" in error_str or "TLS" in error_str or "ssl" in error_str:
        print("💡 É problema de SSL/TLS")
        print("   → IP pode não estar whitelisted")
        print("   → Credenciais podem estar inválidas")
    elif "auth" in error_str.lower():
        print("💡 É problema de autenticação")
        print("   → Verificar se MONGO_URI está correta")
        print("   → Verificar se credenciais são válidas no MongoDB Atlas")
    else:
        print("💡 Erro diferente")
        print(f"   → {error_str}")

# Teste 2: Com certifi
print("\n" + "="*60)
print("Teste 2: Conexão com certifi + tls=True...")

try:
    import certifi
    from pymongo import MongoClient

    client = MongoClient(
        mongo_uri,
        tlsCAFile=certifi.where(),
        tls=True,
        serverSelectionTimeoutMS=5000
    )
    client.admin.command('ping')
    print("✅ Funcionou com certifi + TLS!")

except Exception as e:
    error_str = str(e)
    print(f"❌ Erro com TLS: {error_str[:200]}")

print("\n" + "="*60)
print("DIAGNÓSTICO CONCLUÍDO")
print("\nPróximos passos:")
print("1. Se Teste 1 funcionou → IP/credenciais OK, problema é TLS")
print("2. Se Teste 1 falhou → Problema é IP não whitelisted ou credenciais inválidas")
