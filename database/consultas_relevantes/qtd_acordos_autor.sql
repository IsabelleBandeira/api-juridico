
-- Quantidade de Acordos por Autor (ordenado da maior pra menor)
SELECT COUNT(1) as 'Quantidade de Acordos', aut.nome as 'Autor' FROM Acordo acd with (nolock)
INNER JOIN Autor aut with (nolock) on acd.id_autor = aut.id
GROUP BY aut.id, aut.nome
ORDER BY COUNT(1) DESC

-- Quantidade de Acordos de um Autor específico
SELECT 
	COUNT(1) as 'Quantidade de Acordos' 
FROM Acordo acd with (nolock)
INNER JOIN Autor aut with (nolock) on acd.id_autor = aut.id
WHERE aut.id = 1