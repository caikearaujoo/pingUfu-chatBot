# 🛠️ Atualizações da Engine de RAG (Busca e Resposta)

Esse documento resume as refatorações que fizemos nos scripts da pasta `rag/` e na `main.py` para fazer o bot  buscar dados reais no nosso MongoDB Atlas. 

Basicamente, alinhamos os nomes, evitamos que o código quebre com dados vazios e melhoramos a inteligência da IA.

## O que mudou?

### 1. Limpeza do Repositório (`.gitignore`)
* **O que rolou:** Adicionamos pastas pesadas e sensíveis no `.gitignore` (`.env`, `.venv/`, `.hf_cache/`, `.vscode/`).
* **Por que:** Para evitar vazar as chaves de API do Gemini e do Mongo, e impedir que arquivos gigantes de modelos do HuggingFace pesem o nosso GitHub.

### 2. Atualização da SDK do Google (`main.py`)
* **O que rolou:** Trocamos a biblioteca antiga `langchain-google-genai` pela nova SDK oficial `google-genai`.
* **Por que:** O Google descontinuou o pacote antigo. Agora o código roda sem aquele aviso vermelho gigante de *Deprecation* e está pronto para as atualizações futuras do Gemini.

### 3. Alinhamento de Vetores e Coleções
* **O que rolou:** 
    * Em `embeddings.py`, o modelo foi alterado para `paraphrase-multilingual-MiniLM-L12-v2` (o mesmo usado na ingestão).
  * Em `docs_inst.py` e `professores.py`, corrigimos os nomes dos campos (`vector_embedding` ➡️ `vetor_chunk` e `vetor_unificado`) e das coleções (`docsInstitucionais_chunks`).
* **Por que:** O Mongo é chato com nomes. Se a busca pedir um nome de campo diferente do que foi salvo, ele não acha nada.

### 4. Inteligência do Classificador (`classifier.py`)
* **O que rolou:** Adicionamos uma instrução no prompt para a IA extrair também o `disciplina_nome` e o `codigo_disciplina` da pergunta do usuário.
* **Por que:** O handler estrutural precisa dessas variáveis exatas para filtrar as matérias no banco de dados.

### 5. Mais Resultados na Busca (Top-K)
* **O que rolou:** Os handlers `disciplina_semantica` e `disciplina_estrutural` deixaram de pegar apenas o primeiro resultado (`docs[0]`) e passaram a empilhar o Top 5 e o Top 3 no contexto.
* **Por que:** Se o aluno perguntar "matérias de matemática", o bot precisa ler as ementas de várias disciplinas de exatas simultaneamente para dar uma resposta completa, e não travar só na primeira que achar.

### 6. Proteção contra "Crash" (Tratamento de Erros)
* **O que rolou:** Trocamos a forma de ler os dados dos dicionários, de `d['chave']` para o método seguro `d.get('chave', 'Não informada')`.
* **Por que:** Se o nosso robô raspador não encontrou a área de pesquisa de um professor no site da FACOM, o campo vem vazio. O `.get()` impede que o Python trave o bot inteiro com um `KeyError`.

### 7. Correção das Fontes Mistas (`mixed.py`)
* **O que rolou:** O `handler_mixed_query` agora acumula as fontes (`sources`) de todos os handlers que ele aciona e retorna a lista cheia.
* **Por que:** Antes ele estava retornando uma lista vazia `[]`, o que fazia o bot responder a pergunta, mas não listar de onde tirou a informação no final do chat.

### 8. Busca Híbrida e "Jogo de Cintura" com Acentos (Estrutural)
* **O que rolou:** 
    * Em `rag/retrieval/disciplinas_estrutural.py`, implementamos uma busca **híbrida**: se o aluno digita o código (ex: GBC014), o sistema faz uma busca exata (`$regex`). Se digita o nome ("geometria analitica"), o sistema usa busca vetorial (`$vectorSearch`). 
  * Em `rag/prompts/est_disciplina.py`, alteramos as regras do prompt para avisar a IA que o aluno pode digitar nomes incompletos ou sem acento.
* **Por que:** A busca normal do MongoDB não ignora acentos, então "Analitica" não achava "ANALÍTICA". A busca vetorial resolve isso. Além disso, a IA estava sendo muito rígida: ela achava o documento certo, mas se recusava a responder porque o nome digitado não era *exatamente* igual ao título oficial (ex: "geometria" vs "GEOMETRIA ANALÍTICA E ÁLGEBRA LINEAR"). Agora o bot tem a malícia de fazer essa associação.