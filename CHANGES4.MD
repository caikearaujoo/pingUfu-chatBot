# 🚀 Pipeline de Ingestão de Dados - pingUfu-chatBot

Esse arquivo documenta o pipeline de ingestão de dados do nosso chatbot. Basicamente, é aqui que explicamos como a gente puxa os dados dos professores, as fichas de disciplinas (BCC e BSI) e os documentos da FACOM, dá uma limpada em tudo e joga pro MongoDB pra Inteligência Artificial consultar depois.

## 🛠️ O que rolou nas últimas atualizações (Changelog)

A gente pegou uns erros pesados durante o desenvolvimento, mas a arquitetura atual tá bem robusta. Atualizações:

* **Troca de REGEX por IA Generativa:** Antes a gente tentava cortar os PDFs na marra (procurando palavras chave), mas os PDFs da UFU vêm com muito erro de leitura e variação de layout. Agora a gente manda o texto bruto pro Gemini (no modo JSON) e ele devolve os dados certinhos, já corrigindo erros de português de tabela zoada.
* **Sistema Anti-Queda (Rate Limit):** Como a gente usa a API gratuita do Google, se mandar ler 50 PDFs de uma vez, ele corta a conexão (Erro 429). Colocamos uma lógica de *Exponential Backoff*. Se o Google reclamar, o script pausa uns segundos, respira e tenta de novo sem crashar o terminal.
* **Filtros e Paginação nos Scrapers:** * Pro site dos **Professores**, fizemos um robô que entra no perfil de cada um e salva em `.txt`, porque tentar baixar o PDF do Lattes tava dando bloqueio de IP.
* Pros **Documentos Institucionais**, o script agora sabe clicar em "Próximo" nas páginas do site e tem uma *Lista VIP* e *Lista Negra*, ignorando lixo (tipo foto de evento e lista de presença).
* **Fatiamento de Docs (Parent-Child):** Documentos gigantes (tipo regimentos) gastam muito token. A gente divide eles em pedaços menores (chunks) pro RAG buscar mais rápido, mas mantendo a referência do arquivo original (Pai). Nesse tópico em específico, não conseguimos manter a subdivisão de seções como documentos pais, então utilizamos a subdivisão predefinida mesmo.

---

## ⚙️ Preparando o Terreno (Instalação)

Antes de rodar qualquer coisa, instala as dependências. A gente atualizou os pacotes do LangChain e do Google pra usar as versões mais novas.

Roda isso aqui no terminal:
```bash
pip install pdfplumber requests beautifulsoup4 urllib3 pymongo certifi google-genai langchain langchain-text-splitters langchain-huggingface sentence-transformers python-dotenv
```

Agora, rode os arquivos da pasta downloads separadamente para baixar todos os arquivos referentes ao nome do arquivo.py
```bash
python baixar_docsInst.py
python baixar_professores.py
python baixarFichasPDF.py
```

Após a intalação, basta executar o arquivo populacao.py para iniciar a extração das informações dos arquivos instalados no banco de dados. 
**Não esqueça de verificar se seu IP está vinculado no banco de dados, caso contrário o programa alegará erro.**