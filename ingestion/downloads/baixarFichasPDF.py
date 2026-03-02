import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote

# --- CONFIGURAÇÕES ---
URL_BASE = "https://facom.ufu.br"
PASTA_DESTINO = "pdfs_fichas_facom"
URLS_VISITADAS = set()

# Palavras-chave para identificar os links corretos
# 1. Para sair da Home e ir para o Curso
KEYWORDS_CURSOS = ["bacharelado", "sistemas-de-informacao", "ciencia-da-computacao", "graduacao"]

# 2. Para sair do Curso e ir para as Fichas
KEYWORDS_FICHAS = ["fichas", "componentes curriculares", "disciplinas", "elenco"]

if not os.path.exists(PASTA_DESTINO):
    os.makedirs(PASTA_DESTINO)

def baixar_pdf(url_pdf, curso_contexto="Geral"):
    """
    Baixa o PDF e salva numa subpasta com o nome do curso (opcional, mas organizado).
    """
    try:
        nome_arquivo = os.path.basename(urlparse(url_pdf).path)
        nome_arquivo = unquote(nome_arquivo)
        
        if not nome_arquivo.lower().endswith('.pdf'):
            return

        # Cria uma pasta específica para o curso se quiser organizar melhor
        pasta_final = os.path.join(PASTA_DESTINO, curso_contexto)
        if not os.path.exists(pasta_final):
            os.makedirs(pasta_final)

        caminho_completo = os.path.join(pasta_final, nome_arquivo)

        if os.path.exists(caminho_completo):
            return

        print(f"   ⬇️  [{curso_contexto}] Baixando: {nome_arquivo}...")
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url_pdf, headers=headers, timeout=15)
        
        if response.status_code == 200:
            with open(caminho_completo, 'wb') as f:
                f.write(response.content)
        else:
            print(f"   ❌ Erro status {response.status_code}")

    except Exception as e:
        print(f"   ⚠️ Erro download: {e}")

def obter_soup(url):
    """Função auxiliar para baixar HTML e criar o objeto BeautifulSoup"""
    try:
        if url in URLS_VISITADAS:
            return None
        URLS_VISITADAS.add(url)

        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Erro ao acessar {url}: Status {response.status_code}")
            return None
            
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return None

def vasculhar_fichas():
    print("--- 🚀 INICIANDO ROBÔ DE FICHAS (FACOM) ---")
    
    # ---------------------------------------------------------
    # PASSO 1: Acessar a Home para encontrar os Cursos
    # ---------------------------------------------------------
    print(f"\n📍 NÍVEL 1: Acessando Home ({URL_BASE})...")
    soup_home = obter_soup(URL_BASE)
    if not soup_home: return

    links_cursos_encontrados = set()
    
    # Procura todos os links da home
    for link in soup_home.find_all('a', href=True):
        href = link['href']
        url_completa = urljoin(URL_BASE, href)
        texto_link = link.get_text().lower()

        # Filtro: Se o link tem palavras de curso (BCC ou BSI)
        # E evita links que não sejam da facom
        if "facom.ufu.br" in url_completa:
            if any(k in href.lower() for k in KEYWORDS_CURSOS) or \
               any(k in texto_link for k in KEYWORDS_CURSOS):
                
                # Exclui links que não parecem ser páginas principais de curso (ex: editais, noticias)
                if "noticia" not in url_completa and "editais" not in url_completa:
                    links_cursos_encontrados.add(url_completa)

    print(f"🔎 Encontrados {len(links_cursos_encontrados)} possíveis páginas de cursos.")

    # ---------------------------------------------------------
    # PASSO 2: Entrar em cada Curso para achar a página de "Fichas"
    # ---------------------------------------------------------
    for url_curso in links_cursos_encontrados:
        # Define um nome para o curso baseado na URL (para criar pasta)
        nome_curso = "BCC" if "ciencia" in url_curso else "BSI" if "sistemas" in url_curso else "Outros"
        print(f"\n📍 NÍVEL 2: Visitando Curso: {nome_curso} ({url_curso})")
        
        soup_curso = obter_soup(url_curso)
        if not soup_curso: continue

        encontrou_pagina_fichas = False

        for link in soup_curso.find_all('a', href=True):
            href = link['href']
            url_fichas = urljoin(url_curso, href)
            texto_link = link.get_text().lower()

            # Filtro: Procura links que falam de "Fichas" ou "Disciplinas"
            if any(k in texto_link for k in KEYWORDS_FICHAS) or "fichas" in href:
                print(f"   👉 Achei página de Fichas: {url_fichas}")
                
                # ---------------------------------------------------------
                # PASSO 3: Baixar PDFs dessa página
                # ---------------------------------------------------------
                soup_fichas = obter_soup(url_fichas)
                if soup_fichas:
                    pdfs_na_pagina = soup_fichas.find_all('a', href=True)
                    count_pdfs = 0
                    
                    for link_pdf in pdfs_na_pagina:
                        href_pdf = link_pdf['href']
                        if href_pdf.lower().endswith('.pdf'):
                            url_pdf_final = urljoin(url_fichas, href_pdf)
                            baixar_pdf(url_pdf_final, curso_contexto=nome_curso)
                            count_pdfs += 1
                    
                    if count_pdfs > 0:
                        encontrou_pagina_fichas = True
                        print(f"   ✅ Baixados {count_pdfs} PDFs deste link.")

        if not encontrou_pagina_fichas:
            print("   ⚠️ Nenhuma página de 'Fichas' identificada explicitamente neste curso.")

if __name__ == "__main__":
    vasculhar_fichas()