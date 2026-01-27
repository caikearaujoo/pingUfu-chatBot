Registro de Alterações - Projeto PingUfu ChatBot
Este documento resume as correções estruturais, refatorações de código e implementações de testes realizadas para estabilizar o backend do sistema RAG.

1. Camada de Roteamento e Motor de Resposta
   Arquivo: rag/router.py
   Passagem de Contexto: Adicionado o parâmetro categoria na chamada da função answer_with_llm. Isso garante que o motor de resposta saiba qual prompt específico carregar.

Arquivo: rag/answer_engine.py
Registro de Prompts: Adicionada a chave ESTRUTURAL_DISCIPLINA ao PROMPT_REGISTRY, mapeando-a para o construtor de prompt adequado.

Correção de Importações: Ajustados os imports dos módulos de prompts para refletir a existência de arquivos separados (sem_disciplina.py e est_disciplina.py), utilizando alias (as) para evitar conflitos de nomes.

Arquivo: rag/prompts/
Padronização: Verificação e renomeação de arquivos para garantir consistência entre o nome do arquivo físico e o import no Python (ex: institutional.py).

2. Camada de Recuperação (Retrieval) - Implementação de Lazy Loading
   O problema crítico de falha na inicialização foi resolvido alterando a forma como a conexão com o MongoDB é estabelecida. Anteriormente, a conexão ocorria no momento da importação do arquivo, causando erros se as variáveis de ambiente não estivessem presentes ou se o DNS falhasse (comum em testes).

A lógica foi alterada para Lazy Loading (carregamento tardio) nos seguintes arquivos:

rag/retrieval/docs_inst.py

rag/retrieval/disciplinas_semantica.py

rag/retrieval/disciplinas_estrutural.py

rag/retrieval/professor.py

Mudança Técnica:

Remoção do objeto MongoClient do escopo global.

Criação de funções internas (ex: \_get_collection()) que instanciam o cliente e acessam o banco apenas quando a função de busca é executada pela primeira vez.

Implementação de um padrão Singleton simplificado (variável global \_client ou \_collection) para reutilizar a conexão em chamadas subsequentes.

3. Estratégia de Testes (Integration Tests)
   Arquivo: tests/test_queries.py
   Foi criado um script de teste robusto para validar o fluxo completo (Router -> Handler -> Mock DB -> LLM Mock).

Mock de LLM: Criação da classe MockLLMClient para simular respostas do classificador e da geração de texto, evitando custos de API.

Patching de Banco de Dados: Utilização do decorator @patch da biblioteca unittest.mock. Isso intercepta as chamadas às funções de busca (ex: search_docs_institucionais) e retorna dados falsos, impedindo qualquer tentativa de conexão real com a internet ou banco de dados.

Correção de Esquemas de Dados (Schemas): Ajuste dos dicionários de retorno dos Mocks para incluir campos obrigatórios esperados pelos Handlers, solucionando erros de KeyError:

Institucional: Adicionado doc_titulo.

Disciplina: Adicionados disciplina_obj, disciplina_ementa, disciplina_programa, disciplina_bibliografia, etc.

Professor: Adicionados prof_nome, prof_area, prof_pesquisa, prof_email, etc.

4. Ponto de Entrada da Aplicação
   Arquivo: main.py (Novo)
   Criação do arquivo principal para interação via terminal.

Modo Duplo: Implementação de uma flag USE_MOCK.

True: Utiliza dados simulados e patches, permitindo testar a lógica sem infraestrutura.

False: Conecta-se aos serviços reais (OpenAI e MongoDB Atlas).

Loop Interativo: Interface de linha de comando para envio de perguntas e recebimento de respostas processadas.

Mock Inteligente: Replicação da lógica de patch do arquivo de testes dentro do main.py para garantir que o modo de simulação possua todos os campos de dados necessários para a execução dos Handlers.

Próximos Passos Sugeridos:

Configurar as variáveis de ambiente reais (MONGO_URI, OPENAI_API_KEY) no arquivo .env.

Popular o banco de dados MongoDB Atlas com os dados reais (Institucionais, Disciplinas e Professores).

Alterar USE_MOCK = False no main.py para validar a conexão real.
