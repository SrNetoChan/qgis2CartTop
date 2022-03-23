/*-- Consolidar linestrings da tabela linha de quebra sempre adjaentes
  (em X, Y e Z) e os seus attributos iguais.*/

CREATE SCHEMA IF NOT EXISTS backup;
CREATE TABLE backup.linha_de_quebra_bk (like public.linha_de_quebra);
INSERT INTO backup.linha_de_quebra_bk
SELECT * FROM public.linha_de_quebra;

BEGIN;

CREATE SCHEMA IF NOT EXISTS temp ;
CREATE TABLE temp.linha_de_quebra_temp (like public.linha_de_quebra INCLUDING DEFAULTS);

INSERT INTO temp.linha_de_quebra_temp (
		inicio_objeto,
		valor_classifica,
		valor_natureza_linha,
		artificial,
		geometria)
WITH collect_lines AS (
	SELECT
		valor_classifica,
		valor_natureza_linha,
		artificial,
		ST_COLLECT(geometria) AS geometria
	FROM public.linha_de_quebra cdn
	GROUP BY 
		valor_classifica,
		valor_natureza_linha,
		artificial
	)
	SELECT
		now(),
		valor_classifica,
		valor_natureza_linha,
		artificial,
		(ST_DUMP(st_linemerge(geometria))).geom AS geometria
	FROM collect_lines;

TRUNCATE TABLE public.linha_de_quebra;

INSERT INTO public.linha_de_quebra (
        inicio_objeto,
		valor_classifica,
		valor_natureza_linha,
		artificial,
		geometria)
SELECT
	inicio_objeto,
	valor_classifica,
	valor_natureza_linha,
	artificial,
	geometria
FROM temp.linha_de_quebra_temp cdnt;

DROP TABLE IF EXISTS temp.linha_de_quebra_temp;

END;