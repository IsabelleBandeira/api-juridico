CREATE DATABASE juridico_db;
GO

CREATE LOGIN juridico_app
WITH PASSWORD = 'PLACEHOLDER_PSWD';
GO

USE juridico_db;
GO

CREATE USER juridico_app
FOR LOGIN juridico_app;
GO

ALTER ROLE db_datareader ADD MEMBER juridico_app;
ALTER ROLE db_datawriter ADD MEMBER juridico_app;
GO