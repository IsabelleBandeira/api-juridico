-- Retorna todos os documentos de um acordo e autor
SELECT
	doc.titulo as 'Título do Documento',
	doc.url as 'URL do Documento',
	doc.url_thumbnail as 'URL da Thumbnail',
	acd.titulo as 'Título do Acordo',
	aut.nome as 'Nome do Autor',
	aut.email as 'Email do Autor',
	aut.numero_telefone as 'Telefone do Autor',
	aut.nome_empresa as 'Nome da Empresa',
	aut.segmento_empresa as 'Segmento da Empresa'
FROM Documento doc with (nolock)
INNER JOIN Acordo acd with (nolock) on doc.id_acordo = acd.id
INNER JOIN Autor aut with (nolock) on acd.id_autor = aut.id
WHERE acd.id = 1 and aut.id = 1

-- Alternativa por nome e titulo:
-- WHERE acd.titulo like '%quidem%'
-- AND aut.nome like '%Leanne%'