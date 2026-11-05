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

## 4. Preparação inicial do SQL Server

> **Esta etapa é necessária somente na primeira configuração do banco.** O container do SQL Server inicializa o serviço, mas não executa automaticamente o arquivo `database/criacao_usuario.sql`. O banco `juridico_db` e o login `juridico_app` precisam ser criados antes de executar a criação das tabelas.

### 4.1. Iniciar o SQL Server

Suba os serviços:

```bash
docker compose up -d --build
```

Confira se o SQL Server está em execução:

```bash
docker compose ps
docker compose logs -f sqlserver
```

Aguarde a inicialização completa do SQL Server antes de tentar conectar.

### 4.2. Conectar inicialmente ao banco `master`

Na primeira execução, `juridico_db` ainda não existe. Por isso, a conexão administrativa deve começar pelo banco `master`.

Se tentar conectar usando `juridico_db` como banco inicial, o SSMS poderá informar que a conexão foi interrompida ou que não foi possível abrir o banco. Isso não significa necessariamente que o serviço SQL Server esteja indisponível.

#### Opção A — SQL Server Management Studio (SSMS)

No SSMS, conecte usando:

- **Server name:** `localhost,1433` (ou o endereço/porta publicados no Docker Compose);
- **Authentication:** SQL Server Authentication;
- **Login:** `sa`;
- **Password:** valor de `MSSQL_SA_PASSWORD` configurado no `.env`.

Antes de conectar:

1. Na janela **Connect to Server**, clique em **Options >>**.
2. Abra **Connection Properties**.
3. Em **Connect to database**, informe `master`.
4. Conecte.

Com a conexão aberta, abra o arquivo `database/criacao_usuario.sql`, substitua `PLACEHOLDER_PSWD` pela senha definida em `DATABASE_PASSWORD` no `.env` e execute o script.

O script cria o banco `juridico_db`, o login de servidor `juridico_app`, o usuário correspondente dentro do banco e as permissões de leitura e escrita.

#### Opção B — CMD, PowerShell ou Bash usando `sqlcmd` dentro do container

O container utiliza o `sqlcmd` instalado em `/opt/mssql-tools18/bin/sqlcmd`. Assim, não é necessário instalar o `sqlcmd` na máquina host.

Abra um terminal na pasta do projeto e execute:

```bash
docker compose exec -it sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "SENHA_DO_SA" -C -d master
```

Substitua `SENHA_DO_SA` pelo valor de `MSSQL_SA_PASSWORD` do `.env`.

O parâmetro `-d master` é importante: ele define `master` como banco inicial da conexão, permitindo criar `juridico_db`.

No prompt do `sqlcmd`, execute os comandos abaixo. Substitua `SENHA_DA_APP` pela mesma senha configurada em `DATABASE_PASSWORD` no `.env`:

```sql
CREATE DATABASE juridico_db;
GO

CREATE LOGIN juridico_app
WITH PASSWORD = 'SENHA_DA_APP';
GO

USE juridico_db;
GO

CREATE USER juridico_app
FOR LOGIN juridico_app;
GO

ALTER ROLE db_datareader ADD MEMBER juridico_app;
ALTER ROLE db_datawriter ADD MEMBER juridico_app;
GO
```

Para sair do `sqlcmd`:

```sql
EXIT
```

**Observações sobre o terminal:**

- O comando acima pode ser executado no CMD, PowerShell ou Bash, desde que o Docker Compose esteja disponível.
- O `GO` deve ficar sozinho em uma linha. Ele indica ao `sqlcmd` que o bloco SQL deve ser executado.
- A opção `-P` passa a senha como argumento do comando. Evite compartilhar o comando com a senha preenchida ou salvá-lo em scripts versionados.
- Se o caminho `/opt/mssql-tools18/bin/sqlcmd` não existir na imagem utilizada, verifique se ela possui a versão anterior em `/opt/mssql-tools/bin/sqlcmd`.

### 4.3. Conferir a criação do banco e do login

Ainda no `sqlcmd`, é possível conferir se o banco e o login foram criados:

```sql
SELECT name, state_desc
FROM sys.databases
WHERE name = 'juridico_db';
GO

SELECT name, is_disabled
FROM sys.sql_logins
WHERE name = 'juridico_app';
GO
```

O banco deve aparecer como `ONLINE` e o login deve aparecer com `is_disabled = 0`.

### 4.4. Criar as tabelas da aplicação

Depois de criar o banco e o login, confirme que o `.env` contém os mesmos valores utilizados no script:

```dotenv
DATABASE_HOST=sqlserver
DATABASE_PORT=1433
DATABASE_NAME=juridico_db
DATABASE_USER=juridico_app
DATABASE_PASSWORD=SENHA_DA_APP
```

A criação das tabelas é uma etapa separada da criação do banco e do login. Execute:

```bash
docker compose exec app python -m app.create_tables
```

Esse comando utiliza os modelos SQLAlchemy para criar as tabelas no banco configurado em `DATABASE_NAME`.

O usuário utilizado por `DATABASE_USER` precisa ter permissões para criar as tabelas. Se a execução retornar erro de permissão de DDL, conecte como `sa` ao banco `juridico_db` e conceda a permissão de criação necessária ao usuário da aplicação no ambiente local:

```sql
USE juridico_db;
GO

ALTER ROLE db_ddladmin ADD MEMBER juridico_app;
GO
```

Essa permissão é voltada à inicialização local do schema. Em um ambiente de produção, prefira separar o usuário de migração/schema do usuário de execução da aplicação e conceder somente as permissões necessárias a cada um.

Depois que as tabelas forem criadas, a aplicação poderá ser executada normalmente.

## 5. Executando o projeto

### 4.1. Iniciar os serviços

Com o Docker em execução, suba os serviços:

```bash
docker compose up -d --build
```

Esse comando inicia os serviços de infraestrutura e a API definidos no Docker Compose.

Verifique se os containers estão em execução:

```bash
docker compose ps
```

### 4.2. Executar o Producer

O Producer é executado sob demanda. Para iniciar a ingestão:

```bash
docker compose run --rm producer
```

O Producer consulta a API externa, transforma os dados e publica as mensagens na fila SQS.

### 4.3. Executar o Consumer

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

### 4.4. Consultar a API

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