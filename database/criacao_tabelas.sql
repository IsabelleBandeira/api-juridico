/*
    Script equivalente ao schema criado por app/create_tables.py
    SQL Server 2022

    Execute conectado ao banco configurado em DATABASE_NAME (ex.: juridico_db).
    O script cria as tabelas Autor, Acordo e Documento, suas PKs, constraints
    UNIQUE, FKs e os índices declarados com index=True nos modelos SQLAlchemy.

    Observação: este arquivo é uma representação SQL manual do metadata ORM.
    A aplicação pode continuar usando python -m app.create_tables.
*/

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

IF OBJECT_ID(N'dbo.Autor', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Autor (
        id INT IDENTITY(1,1) NOT NULL,
        codigo_externo INT NOT NULL,
        nome NVARCHAR(200) NOT NULL,
        email NVARCHAR(254) NOT NULL,
        numero_telefone NVARCHAR(50) NOT NULL,
        logradouro NVARCHAR(200) NOT NULL,
        complemento NVARCHAR(200) NULL,
        cidade NVARCHAR(200) NOT NULL,
        cep NVARCHAR(20) NOT NULL,
        nome_empresa NVARCHAR(200) NULL,
        segmento_empresa NVARCHAR(200) NULL,
        CONSTRAINT PK_Autor PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_Autor_codigo_externo UNIQUE (codigo_externo)
    );
END;
GO

IF OBJECT_ID(N'dbo.Acordo', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Acordo (
        id INT IDENTITY(1,1) NOT NULL,
        codigo_externo INT NOT NULL,
        id_autor INT NOT NULL,
        titulo NVARCHAR(200) NOT NULL,
        CONSTRAINT PK_Acordo PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_Acordo_codigo_externo UNIQUE (codigo_externo),
        CONSTRAINT FK_Acordo_Autor FOREIGN KEY (id_autor)
            REFERENCES dbo.Autor (id)
    );
END;
GO

IF OBJECT_ID(N'dbo.Documento', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Documento (
        id INT IDENTITY(1,1) NOT NULL,
        codigo_externo INT NOT NULL,
        id_acordo INT NOT NULL,
        titulo NVARCHAR(200) NOT NULL,
        url NVARCHAR(2048) NOT NULL,
        url_thumbnail NVARCHAR(2048) NULL,
        CONSTRAINT PK_Documento PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_Documento_codigo_externo UNIQUE (codigo_externo),
        CONSTRAINT FK_Documento_Acordo FOREIGN KEY (id_acordo)
            REFERENCES dbo.Acordo (id)
    );
END;
GO

/* Equivalentes a index=True nos campos de FK dos modelos ORM. */
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'ix_Acordo_id_autor'
      AND object_id = OBJECT_ID(N'dbo.Acordo')
)
BEGIN
    CREATE NONCLUSTERED INDEX ix_Acordo_id_autor
        ON dbo.Acordo (id_autor);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'ix_Documento_id_acordo'
      AND object_id = OBJECT_ID(N'dbo.Documento')
)
BEGIN
    CREATE NONCLUSTERED INDEX ix_Documento_id_acordo
        ON dbo.Documento (id_acordo);
END;
GO
