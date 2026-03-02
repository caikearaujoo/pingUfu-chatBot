import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
import urllib3
import unicodedata

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÕES ---
URL_BASE = "https://facom.ufu.br"
URL_DOCUMENTOS_INICIAL = "https://facom.ufu.br/central-de-conteudos/documentos"
PASTA_INSTITUCIONAL = "pdfs_fichas_facom/institucionais"

# --- O SEGURANÇA DA PORTA ---
PALAVRAS_UTEIS = [
    "resolucao", "regimento", "regulamento", "norma", "manual", "guia", 
    "ppc", "projeto pedagogico", "ata", "estatuto", "diretriz", "portaria", "matriz"
]

PALAVRAS_INUTEIS = [
    "resultado", "homologacao", "cronograma", "lista", "presenca", 
    "gabarito", "edital", "cartaz", "evento", "palestra", "certificado", "inscricao", "deferida"
]

if not os.path.exists(PASTA_INSTITUCIONAL):
    os.makedirs(PASTA_INSTITUCIONAL)

def remover_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

def documento_eh_util(texto_contexto):
    """Analisa o texto do bloco inteiro onde o PDF está inserido."""
    texto_limpo = remover_acentos(texto_contexto.lower())
    
    if any(ruim in texto_limpo for ruim in PALAVRAS_INUTEIS):
        return False
        
    if any(boa in texto_limpo for boa in PALAVRAS_UTEIS):
        return True
        
    return False

def descarregar_documentos_institucionais():
    print(f"--- 🚀 INICIANDO EXTRAÇÃO PAGINADA DE INSTITUCIONAIS ---")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    url_atual = URL_DOCUMENTOS_INICIAL
    pagina_num = 1
    total_salvos = 0

    # LOOP DA PAGINAÇÃO (Vai rodar enquanto existir o botão "Próximo")
    while url_atual:
        print(f"\n📍 Analisando Página {pagina_num}: {url_atual}")
        
        try:
            response = requests.get(url_atual, headers=headers, verify=False, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"❌ Erro ao acessar a página: {e}")
            break

        links_encontrados_na_pagina = 0

        # Coleta e filtra os links olhando para a CAIXA (Container) inteira
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            if href.lower().split('?')[0].endswith('.pdf'):
                # Sobe na árvore do HTML para pegar o bloco de texto onde o link está
                container = a.find_parent('div', class_='views-row')
                if not container:
                    container = a.find_parent('article') or a.find_parent('li') or a.find_parent('div')
                
                # Pega todo o texto ao redor do PDF (incluindo títulos como "Resolução nº 3/2022")
                texto_contexto = container.get_text(separator=' ', strip=True) if container else a.get_text(strip=True)
                
                # Passa o contexto inteiro para o Segurança
                if documento_eh_util(texto_contexto):
                    url_completa = urljoin(URL_BASE, href)
                    nome_ficheiro = unquote(url_completa.split('/')[-1])
                    caminho_completo = os.path.join(PASTA_INSTITUCIONAL, nome_ficheiro)
                    
                    if not os.path.exists(caminho_completo):
                        try:
                            resp_pdf = requests.get(url_completa, headers=headers, verify=False, timeout=30)
                            if resp_pdf.status_code == 200:
                                with open(caminho_completo, 'wb') as f:
                                    f.write(resp_pdf.content)
                                print(f"   ✅ Baixado: {nome_ficheiro} (Palavra-chave identificada no contexto)")
                                total_salvos += 1
                            time.sleep(1) # Respiro
                        except Exception as e:
                            print(f"   ❌ Erro ao baixar PDF {nome_ficheiro}: {e}")
                    else:
                        print(f"   ⏭️ Já existe: {nome_ficheiro}")
                    
                    links_encontrados_na_pagina += 1

        print(f"🔎 {links_encontrados_na_pagina} documentos VIPs encontrados na página {pagina_num}.")

        # --- A MÁGICA DA PAGINAÇÃO ---
        # Procura o botão de ir para a próxima página (geralmente tem "próximo" no texto ou title)
        botao_proximo = soup.find('a', title='Ir para a próxima página')
        if not botao_proximo:
            botao_proximo = soup.find('a', string=lambda t: t and 'próximo' in t.lower())
            
        if botao_proximo and botao_proximo.get('href'):
            url_atual = urljoin(URL_BASE, botao_proximo['href'])
            pagina_num += 1
            time.sleep(2) # Pausa entre páginas para não bloquear o IP
        else:
            print("\n🛑 Fim da paginação. Não há mais páginas para visitar.")
            url_atual = None # Quebra o loop while

    print(f"\n🎉 Missão institucional concluída! {total_salvos} novos documentos guardados.")

if __name__ == "__main__":
    descarregar_documentos_institucionais()