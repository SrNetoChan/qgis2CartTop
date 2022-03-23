/*-- Homogeniza os valores de Z das geometrias da tabeka agua_lentica
	Todos os vertices tomam o valor do calculo da moda de todos os valores*/

CREATE SCHEMA IF NOT EXISTS backup;
CREATE TABLE backup.agua_lentica_bk (like public.agua_lentica);
INSERT INTO backup.agua_lentica_bk
SELECT * FROM public.agua_lentica;

BEGIN;

WITH vertices AS (
	SELECT al.identificador, st_z((st_dumppoints(al.geometria)).geom) AS z
	FROM agua_lentica al
	),
moda AS  (
	SELECT identificador,
		MODE() WITHIN GROUP (ORDER BY z) AS moda_z
	FROM vertices
	GROUP BY identificador
	)
UPDATE public.agua_lentica al
SET geometria = st_translate(st_force3d(st_force2d(geometria)), 0, 0, moda_z)
FROM moda m
WHERE m.identificador = al.identificador;

END;