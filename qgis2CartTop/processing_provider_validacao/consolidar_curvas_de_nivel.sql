/*-- Consolidar linestrings da tabela curvas de nível sempre adjaentes
  (em X, Y e Z) e os seus attributos iguais.*/

CREATE SCHEMA IF NOT EXISTS backup;
CREATE TABLE backup.curva_de_nivel_bk (like public.curva_de_nivel);
INSERT INTO backup.curva_de_nivel_bk
SELECT * FROM public.curva_de_nivel;

BEGIN;

CREATE SCHEMA IF NOT EXISTS temp ;
CREATE TABLE temp.curva_de_nivel_temp (like public.curva_de_nivel INCLUDING DEFAULTS);

INSERT INTO temp.curva_de_nivel_temp (
		inicio_objeto,
		valor_tipo_curva,
		geometria)
WITH collect_lines AS (
	SELECT
		valor_tipo_curva,
		ST_COLLECT(geometria) AS geometria
	FROM public.curva_de_nivel cdn
	GROUP BY 
		valor_tipo_curva
	)
	SELECT
		now(),
		valor_tipo_curva,
		(ST_DUMP(st_linemerge(geometria))).geom AS geometria
	FROM collect_lines;

TRUNCATE TABLE public.curva_de_nivel;

INSERT INTO public.curva_de_nivel (
        inicio_objeto,
		valor_tipo_curva,
		geometria)
SELECT
	inicio_objeto,
	valor_tipo_curva,
	geometria
FROM temp.curva_de_nivel_temp cdnt;

DROP TABLE IF EXISTS temp.curva_de_nivel_temp;

END;