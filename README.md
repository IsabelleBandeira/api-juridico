# API - Jurídico Pleno

Projeto de ingestão, armazenamento e consulta de dados de autores, acordos e documentos.

A solução utiliza uma arquitetura baseada em processamento assíncrono por filas: o Producer coleta os dados de uma API externa e os publica no SQS; o Consumer processa as mensagens e persiste os dados no SQL Server; a API disponibiliza os dados armazenados para consulta.

## 1. Arquitetura

### Fluxo de ingestão

1. **Producer:** consulta a API JSONPlaceholder e transforma os dados em mensagens de ingestão.
2. **Amazon SQS:** recebe e armazena as mensagens para processamento assíncrono.
3. **Consumer:** consome as mensagens, valida seu conteúdo e persiste os dados no banco.
4. **SQL Server:** armazena autores, acordos e documentos.

### API de consulta

A API disponibiliza os dados persistidos, permitindo consultar um autor e seus respectivos acordos e documentos.

### Ambiente local

Para execução e testes locais, o projeto utiliza:

- Docker e Docker Compose;
- LocalStack, para simular os serviços AWS utilizados, incluindo SQS;
- SQL Server, como banco de dados;
- FastAPI, para disponibilizar a API;
- Python, para implementação do Producer e Consumer.

> A arquitetura AWS é representada conceitualmente. A execução local utiliza Docker Compose e LocalStack, sem exigir uma conta AWS.

## 2. Pré-requisitos

Antes de executar o projeto, instale:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/);
- Docker Compose (incluído no Docker Desktop);
- Git, caso deseje clonar o repositório.

Certifique-se de que o Docker Desktop esteja em execução.

## 3. Configuração do ambiente

### 3.1. Obter o projeto

Clone o repositório e acesse a pasta:

```bash
git clone <URL_DO_REPOSITORIO>
cd api-juridico
```

### 3.2. Configurar variáveis de ambiente

Crie o arquivo `.env` a partir do modelo disponibilizado:

```powershell
Copy-Item .env.example .env
```

Configure os valores necessários no arquivo `.env`, especialmente:

- Credenciais e configurações de conexão com o SQL Server;
- Configurações do LocalStack e da fila SQS;
- Chave de autenticação da API (`API_KEY`);
- Nível de log, quando aplicável.

**Importante:** não compartilhe o arquivo `.env` nem envie credenciais reais ao repositório.

## 4. Criação do schema do banco

O SQL Server é executado pelo Docker Compose. As tabelas são criadas pela aplicação por meio dos modelos SQLAlchemy, usando `app/create_tables.py`.

Depois que o SQL Server estiver disponível e o banco configurado em `DATABASE_NAME` existir, execute:

```powershell
docker compose exec app python -m app.create_tables
```

Esse comando cria as tabelas `Autor`, `Acordo` e `Documento`, incluindo chaves primárias, restrições de unicidade, chaves estrangeiras e índices definidos nos modelos. A operação é segura para execução repetida: `create_all` cria objetos ausentes e não recria tabelas existentes.

Como alternativa/documentação do mesmo schema, o repositório disponibiliza `database/criacao_tabelas.sql`. Esse script SQL representa manualmente a estrutura declarada nos modelos ORM, incluindo os índices dos campos de relacionamento. Para utilizá-lo, conecte-se ao banco configurado em `DATABASE_NAME` e execute o arquivo. Use **uma** das alternativas para criar as tabelas; não é necessário executar ambas.

> A criação do schema não é executada automaticamente pelo `docker compose up`. Execute o comando acima antes de iniciar a ingestão ou utilizar os endpoints que consultam o banco.

## 5. Executando o projeto

### 5.1. Iniciar os serviços

Com o Docker em execução, suba os serviços:

```bash
docker compose up -d --build
```

Esse comando inicia os serviços de infraestrutura e a API definidos no Docker Compose.

Verifique se os containers estão em execução:

```bash
docker compose ps
```

### 5.2. Executar o Producer

O Producer é executado sob demanda. Para iniciar a ingestão:

```bash
docker compose run --rm producer
```

O Producer consulta a API externa, transforma os dados e publica as mensagens na fila SQS.

### 5.3. Executar o Consumer

O Consumer permanece em execução contínua, aguardando mensagens na fila.

Caso não tenha sido iniciado automaticamente:

```bash
docker compose up -d consumer
```

Acompanhe o processamento:

```bash
docker compose logs -f consumer
```

Após a publicação das mensagens pelo Producer, o Consumer deverá recebê-las, processá-las e persistir os dados no SQL Server.

### 5.4. Dead-letter queue (DLQ)

O script em `scripts/` inicializa a fila principal `juridico-queue` e a fila de mensagens não processadas `juridico-dlq`. A política de redrive configura `maxReceiveCount=3`: mensagens que continuam falhando após as tentativas de entrega são encaminhadas à DLQ.

Para inspecionar as filas no ambiente local, utilize o AWS CLI dentro do container LocalStack, por exemplo:

```bash
docker compose exec localstack awslocal sqs list-queues
docker compose exec localstack awslocal sqs get-queue-attributes \
  --queue-url http://localhost:4566/000000000000/juridico-dlq \
  --attribute-names ApproximateNumberOfMessages
```

### 5.5. Consultar a API

Com a API em execução, acesse a documentação interativa:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI: `http://localhost:8000/openapi.json`

A consulta principal é:

```http
GET /api/v1/autor/{autor_id}/acordos
```

A API exige autenticação por API Key, enviada no cabeçalho `X-API-Key`.

Exemplo utilizando cURL:

```bash
curl -X GET "http://localhost:8000/api/v1/autor/1/acordos" \
  -H "X-API-Key: SUA_API_KEY"
```

Substitua `SUA_API_KEY` pelo valor configurado no `.env`.

A resposta contém os dados do autor, seus acordos e os documentos associados.

## 6. Executando os testes

Para executar toda a suíte de testes:

```bash
docker compose exec app pytest -v
```

Os testes cobrem:

- Validação dos modelos de mensagem;
- Conexão com o banco de dados;
- Cenários da API, incluindo autenticação, validação e autor inexistente;
- Processamento e exclusão de mensagens SQS;
- Tratamento de falhas durante o processamento;
- Idempotência da persistência;
- Rollback de transações em caso de erro.

> Os testes que dependem de serviços externos ou do banco precisam do ambiente correspondente em execução.

A criação do schema pode ser validada consultando as tabelas e índices no SQL Server. O arquivo `database/criacao_tabelas.sql` também serve como referência do DDL correspondente aos modelos.

## 7. Comandos úteis

### Docker Compose

| Comando | Descrição |
|---|---|
| `docker compose up -d` | Inicia os serviços em segundo plano |
| `docker compose down` | Para e remove os containers |
| `docker compose ps` | Lista os serviços e seus estados |
| `docker compose restart` | Reinicia os serviços |
| `docker compose build` | Reconstrói as imagens |
| `docker compose up -d --build` | Reconstrói as imagens e inicia os serviços |

### Logs

| Comando | Descrição |
|---|---|
| `docker compose logs` | Exibe os logs dos serviços |
| `docker compose logs -f` | Acompanha os logs em tempo real |
| `docker compose logs -f consumer` | Acompanha os logs do Consumer |
| `docker compose logs -f app` | Acompanha os logs da API |
| `docker compose logs --tail=100 consumer` | Exibe as últimas 100 linhas do Consumer |

### Producer e Consumer

| Comando | Descrição |
|---|---|
| `docker compose run --rm producer` | Executa o Producer uma vez |
| `docker compose up -d consumer` | Inicia o Consumer em segundo plano |
| `docker compose restart consumer` | Reinicia o Consumer |
| `docker compose stop consumer` | Para o Consumer |

### Testes e terminal

| Comando | Descrição |
|---|---|
| `docker compose exec app pytest -v` | Executa os testes |
| `docker compose exec app pytest tests/test_author.py -v` | Executa os testes da API |
| `docker compose exec app pytest tests/test_consumer.py -v` | Executa os testes do Consumer |
| `docker compose exec app bash` | Abre um terminal no container da API |

### Limpeza do ambiente

```bash
docker compose down
```

Para remover também os volumes persistentes:

```bash
docker compose down -v
```

> Atenção: `docker compose down -v` remove os volumes associados ao ambiente e pode apagar os dados persistidos no banco.


## 8. Encerrando o ambiente

Ao terminar a execução:

```bash
docker compose down
```

Os dados persistidos em volumes Docker são mantidos, salvo se os volumes forem explicitamente removidos.