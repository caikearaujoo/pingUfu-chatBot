# Documentação da Arquitetura RAG – pingUFU Chatbot

## 1. Visão Geral do Projeto

Este projeto implementa um chatbot acadêmico para a UFU baseado em **RAG (Retrieval-Augmented Generation)**. O objetivo principal é responder perguntas acadêmicas de forma **confiável, rastreável e semanticamente correta**, evitando alucinações do LLM e respeitando a natureza dos dados (institucionais, acadêmicos e estruturais).

A arquitetura foi desenhada para separar claramente **responsabilidades**, permitindo evolução incremental, depuração simples e manutenção a longo prazo.

---

## 2. Princípios Arquiteturais

As decisões tomadas seguem alguns princípios fundamentais:

- Separação clara entre **classificação**, **recuperação**, **orquestração** e **geração**
- Cada tipo de pergunta consulta apenas as **collections adequadas**
- O LLM nunca decide _onde_ buscar dados, apenas _como responder_
- Respostas institucionais são protegidas contra truncamento e inferência indevida
- O sistema é extensível para novas categorias sem refatorações grandes

---

## 3. Organização das Pastas

```
rag/
 ├── router.py
 ├── classifier.py
 ├── answer_engine.py
 ├── embeddings.py
 ├── handlers/
 │   ├── institucional.py
 │   ├── disciplina_semantica.py
 │   ├── disciplina_estrutural.py
 │   ├── professor_semantico.py
 │   └── mixed.py
 ├── retrieval/
 │   ├── docs_inst.py
 │   ├── disciplinas.py
 │   └── professores.py
 └── prompts/
     ├── institutional.py
     ├── disciplina.py
     ├── professor.py
     └── mixed.py
```

A seguir, o papel de cada camada.

---

## 4. Classificação (`classifier.py`)

Responsável por **interpretar semanticamente a pergunta do usuário** antes de qualquer busca.

Funções principais:

- Determinar a **categoria da pergunta** (INSTITUCIONAL, SEMANTICA_DISCIPLINA, etc.)
- Extrair metadados relevantes como `curso_alvo` e `intencao`

Motivo da existência:

- Evitar buscas desnecessárias
- Definir corretamente **qual estratégia de RAG** usar
- Garantir que cada pergunta seja tratada no domínio correto

O classificador é intencionalmente simples e determinístico (temperature = 0).

---

## 5. Router (`router.py`)

O router é o **orquestrador central** do sistema.

Responsabilidades:

1. Receber a pergunta do usuário
2. Acionar o classificador
3. Selecionar o handler correto
4. Centralizar a chamada ao LLM
5. Padronizar a resposta final

Decisão importante:

- **Handlers não chamam o LLM**
- O LLM é chamado apenas no router, garantindo controle total sobre geração

Isso evita acoplamento excessivo e facilita testes e logs.

---

## 6. Handlers (`handlers/`)

Cada handler representa **um tipo de intenção semântica**.

### 6.1 INSTITUCIONAL

- Consulta documentos oficiais
- Usa Parent–Child Indexing
- Busca vetorial ocorre nos chunks filhos
- Retorna o chunk pai completo

Motivo:

- Evitar respostas truncadas
- Garantir integridade normativa

### 6.2 SEMANTICA_DISCIPLINA

- Perguntas sobre conteúdo, ementa e aprendizado
- Documento inteiro da disciplina
- Single chunk

### 6.3 ESTRUTURAL_DISCIPLINA

- Dados formais: carga horária, pré-requisitos, semestre
- Predominantemente lookup estruturado

### 6.4 SEMANTICA_PROFESSOR

- Perfil acadêmico e áreas de pesquisa
- Busca vetorial simples
- Retorna perfil completo

### 6.5 MISTA

- Combina múltiplos domínios
- Executa buscas independentes
- Consolida o contexto

Motivo da separação:

- Cada handler conhece **apenas seu domínio**
- Facilita evolução e depuração

---

## 7. Retrieval (`retrieval/`)

Camada responsável exclusivamente por **acesso aos dados**.

Características:

- Nenhuma lógica de negócio
- Nenhuma chamada ao LLM
- Apenas consultas ao MongoDB (vetorial ou estruturada)

Essa separação garante:

- Reutilização
- Testes isolados
- Substituição futura do banco sem refatorar handlers

---

## 8. Prompts (`prompts/`)

Cada categoria possui um **prompt mínimo e restritivo**.

Motivos para separar prompts:

- Clareza semântica
- Evitar prompts genéricos que causam alucinação
- Facilitar ajustes finos por domínio

Os prompts seguem regras comuns:

- Uso exclusivo do contexto
- Proibição explícita de invenção
- Linguagem adequada ao domínio

---

## 9. Answer Engine (`answer_engine.py`)

Responsável por:

- Selecionar o prompt correto com base na categoria
- Executar a chamada ao LLM
- Retornar apenas o texto final

Ele **não conhece retrieval, handlers ou banco de dados**.

Isso mantém a geração desacoplada do restante do sistema.

---

## 10. Por que essa arquitetura funciona

- Evita alucinação
- Mantém rastreabilidade
- Permite escalar categorias
- Facilita auditoria acadêmica
- É compatível com produção

Este não é um RAG genérico, mas um **RAG orientado por domínio**.

---

## 11. Próximos Passos do Desenvolvimento

1. Testar perguntas reais por categoria
2. Criar logs de contexto e score para debug
3. Implementar tratamento explícito de SOCIAL_SAUDACAO e OUT_OF_SCOPE
4. Adicionar testes unitários por handler
5. Refinar prompts com base em falhas reais
6. Criar documentação técnica para onboarding

---

## 12. Conclusão

O sistema atual já possui base arquitetural sólida e alinhada com boas práticas de RAG.

A partir deste ponto, o foco deixa de ser estrutura e passa a ser **qualidade de resposta e confiabilidade**.
