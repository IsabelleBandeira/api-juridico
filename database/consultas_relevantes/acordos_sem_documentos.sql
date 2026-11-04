
-- Quantidade Total de Acordos sem Documentos
SELECT
	COUNT(1) as 'Quantidade de Acordos sem Documentos'
FROM Acordo acd WITH (NOLOCK)
LEFT JOIN Documento doc WITH (NOLOCK) ON doc.id_acordo = acd.id
WHERE doc.id IS NULL

-- Listar os Acordos sem Documentos
SELECT
    acd.titulo AS 'Titulo do Acordo'
FROM Acordo acd WITH (NOLOCK)
LEFT JOIN Documento doc WITH (NOLOCK) ON doc.id_acordo = acd.id
WHERE doc.id IS NULL
