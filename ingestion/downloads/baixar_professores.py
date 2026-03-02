import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3

# Desabilita alertas chatos de SSL que a UFU costuma disparar
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÕES ---
URL_BASE = "https://facom.ufu.br"
URL_DOCENTES = "https://facom.ufu.br/corpo-docente"
PASTA_PROFESSORES = "pdfs_fichas_facom/professores"

if not os.path.exists(PASTA_PROFESSORES):
    os.makedirs(PASTA_PROFESSORES)

def vasculhar_professores_profundo():
    print(f"--- 🚀 INICIANDO EXTRAÇÃO BLINDADA DE PROFESSORES ---")
    
    # Um User-Agent de navegador real para evitar bloqueios
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    try:
        # verify=False impede que o Python trave por causa de certificados da UFU
        response = requests.get(URL_DOCENTES, headers=headers, verify=False, timeout=15)
        soup_lista = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"❌ Erro ao acessar a página principal: {e}")
        return

    # Mapeia todos os links únicos que levam para um perfil
    links_perfis = set()
    for a in soup_lista.find_all('a', href=True):
        href = a['href']
        if '/pessoas/' in href and 'egresso' not in href:
            links_perfis.add(urljoin(URL_BASE, href))

    print(f"🔎 Encontrados {len(links_perfis)} links únicos. Iniciando o download de dados...\n")

    salvos = 0
    for url_perfil in links_perfis:
        try:
            # Aumentei o timeout para 30s para evitar o erro da prof. Marcia
            resp_perfil = requests.get(url_perfil, headers=headers, verify=False, timeout=30)
            soup_perfil = BeautifulSoup(resp_perfil.text, 'html.parser')

            # 1. A ESTRATÉGIA BLINDADA PARA O NOME DO ARQUIVO
            # Pegamos a última parte da URL (ex: "adriano-rocha" de /pessoas/docentes/adriano-rocha)
            slug_url = url_perfil.split('/')[-1]
            if not slug_url: # Se por acaso terminar em barra, pega o penúltimo
                slug_url = url_perfil.split('/')[-2]
                
            # O nome do arquivo será SEMPRE o final da URL (Garante que nunca vai sobrescrever)
            nome_arquivo = f"{slug_url}.txt"
            
            # O nome de exibição dentro do texto
            nome_professor = slug_url.replace("-", " ").title()

            # 2. Busca o Conteúdo Principal
            area_conteudo = soup_perfil.find('div', class_='region-content')
            if not area_conteudo:
                area_conteudo = soup_perfil.find('main')
            if not area_conteudo:
                area_conteudo = soup_perfil.find('body')

            texto_perfil_completo = area_conteudo.get_text(separator='\n', strip=True) if area_conteudo else "Sem conteúdo estruturado."

            # 3. Caminho completo para salvar
            caminho_completo = os.path.join(PASTA_PROFESSORES, nome_arquivo)
            
            # 4. Monta o Dossiê Final
            dossie = f"NOME: {nome_professor}\n"
            dossie += f"URL PERFIL FACOM: {url_perfil}\n"
            dossie += "="*40 + "\n"
            dossie += "CONTEÚDO COMPLETO DO PERFIL:\n\n"
            dossie += texto_perfil_completo
            
            # 5. SALVA NO HD
            with open(caminho_completo, 'w', encoding='utf-8') as f:
                f.write(dossie)
                
            print(f"   ✅ Salvo com sucesso: {nome_arquivo}")
            salvos += 1
            
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Erro ao processar o perfil em {url_perfil}: {e}")

    print(f"\n🎉 Missão cumprida! {salvos} dossiês foram salvos na pasta '{PASTA_PROFESSORES}'.")

if __name__ == "__main__":
    vasculhar_professores_profundo()