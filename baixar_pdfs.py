import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote

# --- CONFIGURAÇÕES ---
URL_BASE = "https://facom.ufu.br"
PASTA_DESTINO = "pdfs_facom"
urls_visitadas = set()

# Extensões que queremos ignorar para ganhar velocidade
EXTENSOES_IGNORAR = ('.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.ico', '.xml')

if not os.path.exists(PASTA_DESTINO):
    os.makedirs(PASTA_DESTINO)

def limpar_url(url):
    """Remove a parte do # (âncora) para evitar duplicidade"""
    return url.split('#')[0].rstrip('/')

def baixar_pdf(url_pdf):
    try:
        nome_arquivo = os.path.basename(urlparse(url_pdf).path)
        nome_arquivo = unquote(nome_arquivo)
        
        if not nome_arquivo.lower().endswith('.pdf'):
            return

        caminho_completo = os.path.join(PASTA_DESTINO, nome_arquivo)

        if os.path.exists(caminho_completo):
            # Comentado para poluir menos o terminal, descomente se quiser ver
            # print(f"⚠️  Já existe: {nome_arquivo}") 
            return

        print(f"⬇️  BAIXANDO: {nome_arquivo}...")
        
        response = requests.get(url_pdf, timeout=15)
        if response.status_code == 200:
            with open(caminho_completo, 'wb') as f:
                f.write(response.content)
        else:
            print(f"❌ Erro status {response.status_code}")

    except Exception:
        pass # Ignora erros de download para não parar o robô

def varrer_site(url_atual, profundidade=0):
    # Limita a profundidade para ele não tentar baixar a internet inteira
    if profundidade > 3: 
        return

    url_limpa = limpar_url(url_atual)
    
    if url_limpa in urls_visitadas:
        return
    urls_visitadas.add(url_limpa)

    print(f"🔎 Vasculhando (Nível {profundidade}): {url_limpa}")

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # Verifica se é arquivo de imagem/video antes de baixar o HTML inteiro
        if url_limpa.lower().endswith(EXTENSOES_IGNORAR):
            return

        response = requests.get(url_limpa, headers=headers, timeout=10)
        
        if "text/html" not in response.headers.get('Content-Type', ''):
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)

        for link in links:
            href = link['href']
            url_completa = urljoin(url_atual, href)
            url_completa_limpa = limpar_url(url_completa)

            # 1. Se for PDF -> Baixa
            if url_completa_limpa.lower().endswith('.pdf'):
                baixar_pdf(url_completa_limpa)
            
            # 2. Se for link interno -> Navega (Recursividade)
            elif "facom.ufu.br" in url_completa_limpa and "mailto:" not in url_completa_limpa:
                if url_completa_limpa not in urls_visitadas:
                    varrer_site(url_completa_limpa, profundidade + 1)

    except Exception as e:
        print(f"⚠️ Erro ao ler: {e}")

if __name__ == "__main__":
    print(f"--- INICIANDO ROBÔ OTIMIZADO ---")
    varrer_site(URL_BASE)