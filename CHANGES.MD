# Arquitetura e Evolução do Backend RAG do PingUFU

Este documento descreve, de forma objetiva e técnica, as decisões, correções e evoluções realizadas no backend do sistema **PingUFU**, ao longo do processo de implementação de um pipeline de **RAG (Retrieval-Augmented Generation)**.

O foco foi alinhar código, arquitetura e documentação teórica, garantindo consistência entre:

- Modelo de dados NoSQL
- Estratégia de vetorização
- Organização de pastas
- Pipeline de classificação, recuperação e geração

---

## 1. Contexto Inicial

O backend original possuía:

- Scripts de ingestão de dados estruturados (cursos, disciplinas, professores)
- Ingestão de PDFs institucionais em uma collection única
- Vetorização direta de documentos sem separação clara entre responsabilidade de ingestão, recuperação e geração

Além disso, parte da lógica existia apenas em documentação (Docs), não refletida no código executável.

---

## 2. Correção da Estratégia de Vetorização (Parent-Child Indexing)

Foi adotada explicitamente a estratégia de **Parent-Child Indexing**, especialmente para documentos institucionais.

### 2.1 Conceito aplicado

- **Documento pai**: entidade lógica (ex: Manual de Estágio)
- **Documentos filhos**: chunks do texto, individualmente vetorizados

Apenas os _filhos_ são vetorizados e utilizados na busca semântica. O documento pai serve como contexto lógico, não como vetor.

### 2.2 Aplicação prática

Na collection `DocsInst`:

- Cada chunk do PDF gera um documento
- O campo `vector_embedding` existe apenas nos chunks
- Metadados como `doc_titulo`, `doc_tipo`, `curso_alvo` e `doc_anoVigencia` são replicados em cada chunk

Essa abordagem melhora:

- Precisão da busca
- Relevância do contexto retornado
- Escalabilidade do RAG

---

## 3. Separação Clara de Responsabilidades

Foi definida uma arquitetura em camadas, evitando acoplamento indevido.

### 3.1 Classificação (Router)

Responsável apenas por:

- Receber a pergunta
- Classificá-la semanticamente via LLM

Categorias:

- INSTITUCIONAL
- SEMANTICA_DISCIPLINA
- ESTRUTURAL_DISCIPLINA
- SEMANTICA_PROFESSOR
- MISTA

---

### 3.2 Handlers

Cada handler:

- Executa **somente recuperação de dados**
- Não chama LLM
- Retorna sempre:

```
{
  "contexto": str,
  "sources": list
}
```

Exemplo:

- `handle_institucional` → busca em `DocsInst`
- `handle_disciplina_semantica` → busca vetorial em disciplinas
- `handle_disciplina_estrutural` → consulta estruturada

---

### 3.3 Answer Engine

Foi criado um nível superior responsável exclusivamente por:

- Construir prompts
- Chamar o LLM
- Gerar a resposta final

Arquivo:

```
rag/answer_engine.py
```

Isso garante:

- Centralização da lógica de geração
- Facilidade para troca de modelo
- Padronização das respostas

---

## 4. Router como Orquestrador Central

O `router.py` passou a:

1. Classificar a pergunta
2. Selecionar o handler correto
3. Receber contexto e fontes
4. Chamar o `answer_engine`
5. Retornar resposta final

O router **não** realiza busca direta nem geração textual.

---

## 5. Organização de Pastas

Estrutura final adotada:

```
rag/
├── router.py
├── classifier.py
├── answer_engine.py
│
├── handlers/
│   ├── institucional.py
│   ├── disciplina_semantica.py
│   ├── disciplina_estrutural.py
│   ├── professor_semantico.py
│   └── mixed.py
│
├── retrieval/
│   ├── docs_inst.py
│   ├── disciplinas.py
│   └── professores.py
│
├── embeddings.py
```

Cada pasta possui uma responsabilidade única, evitando dependências circulares.

---

## 6. Scripts Auxiliares

### 6.1 Download de PDFs

O script `baixar_pdfs.py` é considerado **infraestrutura de ingestão**, não parte do pipeline RAG em runtime.

Local recomendado:

```
scripts/ingestion/baixar_pdfs.py
```

### 6.2 Ingestão Completa

O script de ingestão:

- Popula MongoDB
- Gera embeddings
- Cria base vetorial

Executado apenas offline ou em pipeline de dados.

---

## 7. Benefícios da Arquitetura Final

- Separação clara entre retrieval e generation
- Arquitetura compatível com RAG moderno
- Facilidade de manutenção
- Coerência entre documentação teórica e código
- Estrutura defensável academicamente

---

## 8. Conclusão

As mudanças realizadas transformaram um conjunto de scripts isolados em um **sistema RAG estruturado**, com camadas bem definidas, alinhado a boas práticas de engenharia de software e IA aplicada.

Esse desenho permite evolução incremental, inclusão de novas categorias e melhoria contínua da qualidade das respostas, sem necessidade de refatorações profundas.
