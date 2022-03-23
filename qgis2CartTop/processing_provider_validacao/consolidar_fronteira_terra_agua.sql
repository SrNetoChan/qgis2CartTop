/*-- Consolidar linestrings da tabela fronteira terra-agua sempre adjaentes
  (em X, Y e Z) e os seus attributos iguais.*/

CREATE SCHEMA IF NOT EXISTS backup;
CREATE TABLE backup.fronteira_terra_agua_bk (like public.fronteira_terra_agua);
INSERT INTO backup.fronteira_terra_agua_bk
SELECT * FROM public.fronteira_terra_agua;

BEGIN;

CREATE SCHEMA IF NOT EXISTS temp ;
CREATE TABLE temp.fronteira_terra_agua_temp (like public.fronteira_terra_agua INCLUDING DEFAULTS);

INSERT INTO temp.fronteira_terra_agua_temp (
		inicio_objeto,
		data_fonte_dados,
		ilha,
		geometria)
WITH collect_lines AS (
	SELECT
		data_fonte_dados,
		ilha,
		ST_COLLECT(geometria) AS geometria
	FROM public.fronteira_terra_agua cdn
	GROUP BY 
		data_fonte_dados,
		ilha
	)
	SELECT
		now(),
		data_fonte_dados,
		ilha,
		(ST_DUMP(st_linemerge(geometria))).geom AS geometria
	FROM collect_lines;

TRUNCATE TABLE public.fronteira_terra_agua;

INSERT INTO public.fronteira_terra_agua (
        inicio_objeto,
		data_fonte_dados,
		ilha,
		geometria)
SELECT
	inicio_objeto,
	data_fonte_dados,
	ilha,
	geometria
FROM temp.fronteira_terra_agua_temp cdnt;

DROP TABLE IF EXISTS temp.fronteira_terra_agua_temp;

END;