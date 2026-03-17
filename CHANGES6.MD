🚀 Arquitetura Web & API - Projeto PingUfu

Este documento detalha a transição do PingUfu de um script local de terminal (CLI) para uma arquitetura baseada em REST API, permitindo a integração com o novo frontend web (React/Lovable).
1. O que mudou? (Visão Geral)

    Descontinuação do WhatsApp: Para viabilizar o MVP de forma ágil e sem custos de infraestrutura/API da Meta, a interface do usuário migrou para uma aplicação Web.

    Fim do Terminal Loop: O script main.py não utiliza mais o while True para interações via terminal.

    Adoção do FastAPI: O backend foi reescrito para subir um servidor web assíncrono utilizando FastAPI e Uvicorn.

    Comunicação JSON: A aplicação agora se comunica via requisições HTTP (POST), devolvendo respostas estruturadas para o frontend desenhar a UI (incluindo as fontes de RAG).

2. Atualizações no Backend (Python)
Novas Dependências (requirements.txt)

Para suportar o servidor web e a tipagem de dados, foram adicionadas:

    fastapi (Framework Web)

    uvicorn (Servidor ASGI)

    pydantic (Validação de contratos de dados)

    google-genai (Nova SDK oficial do Gemini, atualizada)

Configuração de CORS

O backend agora possui um middleware de CORS (CORSMiddleware) configurado com allow_origins=["*"]. Isso permite que o frontend local (localhost:5173 ou 8080) consiga realizar o fetch sem ser bloqueado pelo navegador.
3. Contrato da API (Endpoints)

A API roda por padrão em http://localhost:8000. A documentação interativa (Swagger) é gerada automaticamente e pode ser acessada em /docs.
🟢 POST /api/chat

Endpoint principal responsável por receber a dúvida do aluno, processar no motor RAG e devolver a resposta formatada.
Payload de Envio (Request)

O frontend deve enviar o seguinte JSON:
JSON

{
  "pergunta": "Quantas horas de estágio preciso para me formar no BSI?",
  "chat_id": null
}

Nota: chat_id está definido como null na V1. A funcionalidade de histórico de conversação está mapeada para a V2.
Payload de Retorno (Response)

O backend processa a pergunta e retorna a resposta da IA acompanhada das fontes utilizadas, essencial para o princípio de transparência do RAG:
JSON

{
  "resposta_ia": "Para se formar no BSI, você precisa cumprir 300 horas de Estágio Curricular Obrigatório...",
  "fontes": [
    {
      "titulo": "Manual de Estágio FACOM - BSI",
      "link": null
    },
    {
      "titulo": "Prof. João Silva",
      "link": "http://lattes.cnpq.br/123456789"
    }
  ],
  "chat_id": null
}

4. Integração Frontend (React)

A interface de usuário agora consome o endpoint /api/chat.

Principais comportamentos implementados no Front:

    Estado de Loading: Exibição de indicador visual ("digitando...") enquanto aguarda a resolução do fetch.

    Renderização de Markdown: A resposta_ia é tratada para exibir negritos, listas e quebras de linha corretamente.

    Componente de Fontes Consultadas: Utiliza o array fontes para listar de onde a IA retirou a informação.

        Se o link for null, exibe apenas o texto.

        Se houver um link (ex: Lattes), o título se torna uma tag <a> clicável com target="_blank".

5. Próximos Passos (Backlog - V2)

    Implementar a collection historico_chats no MongoDB.

    Atualizar o chat_id no frontend para gerar um UUID no primeiro acesso.

    Fazer o motor RAG recuperar as últimas N mensagens atreladas ao chat_id e injetá-las no contexto do LLM para criar "memória" conversacional.

Você quer que eu já escreva o código da classe que vai cuidar dessa feature de histórico no MongoDB (Backlog da V2), ou quer focar em rodar e testar tudo isso junto primeiro?
