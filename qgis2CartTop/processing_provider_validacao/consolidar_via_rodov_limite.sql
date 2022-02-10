/*-- Consolidar linestrings da tabela limites de via rodoviaria sempre que adjaentes
  (em X, Y e Z) e os seus attributos iguais. Por existirem atributos dependentes
  de ligações com outras tabelas, também essas ligações têm de ser acauteladas*/


/* Guardar camadas originais em backup */
CREATE SCHEMA IF NOT EXISTS backup;

CREATE TABLE backup.via_rodov_limite_bk (like public.via_rodov_limite);
INSERT INTO backup.via_rodov_limite_bk
SELECT * FROM public.via_rodov_limite;

CREATE TABLE backup.lig_segviarodov_viarodovlimite_bk (like public.lig_segviarodov_viarodovlimite);
INSERT INTO backup.lig_segviarodov_viarodovlimite_bk
SELECT * FROM public.lig_segviarodov_viarodovlimite;

BEGIN;


/* Unir todas as linhas com atributos iguais, guardando em arrays as ligações a outras
   tabelas*/
CREATE SCHEMA IF NOT EXISTS temp ;
CREATE TABLE temp.via_rodov_limite_temp (like public.via_rodov_limite INCLUDING DEFAULTS);

ALTER TABLE temp.via_rodov_limite_temp 
ADD COLUMN seg_via_rodov_agg uuid[];

INSERT INTO temp.via_rodov_limite_temp (
    inicio_objeto,
	valor_tipo_limite,
	geometria,
	seg_via_rodov_agg)
WITH via_rodov_agg AS
(SELECT lsv.via_rodov_limite_id , array_agg(DISTINCT lsv.seg_via_rodov_id) AS seg_via_rodov_agg
 FROM public.lig_segviarodov_viarodovlimite lsv
 GROUP BY lsv.via_rodov_limite_id)
 , multilines AS (
SELECT
	valor_tipo_limite,
	st_collect(vrl.geometria) AS geometria,
	seg_via_rodov_agg
FROM public.via_rodov_limite vrl 
	LEFT JOIN via_rodov_agg vra ON (vra.via_rodov_limite_id = vrl.identificador)
GROUP BY
	valor_tipo_limite,
	seg_via_rodov_agg
	)
SELECT 
	now(),
	valor_tipo_limite,
	(ST_DUMP(st_linemerge(geometria))).geom AS geometria,
	seg_via_rodov_agg
FROM multilines;

CREATE INDEX ON temp.via_rodov_limite_temp (identificador);
CREATE INDEX ON temp.via_rodov_limite_temp USING gist(geometria);

/*-- Reunir pontos de intersecção entre linhas para cortar entroncamentos e cruzamentos 
	ao mesmo nível */

DROP TABLE IF EXISTS temp.cutting_temp;

CREATE TABLE temp.cutting_temp as
	SELECT 
		(st_dump(st_collect(st_endpoint(geometria),st_startpoint(geometria)))).geom AS geometria 
	FROM temp.via_rodov_limite_temp;

CREATE INDEX ON  temp.cutting_temp USING GIST(geometria);

/* cortar linhas previamente unidas com os pontos de corte */

CREATE TABLE temp.via_rodov_limite_cortados (like temp.via_rodov_limite_temp INCLUDING DEFAULTS);

INSERT INTO temp.via_rodov_limite_cortados (
	inicio_objeto,
	valor_tipo_limite,
	geometria,
	seg_via_rodov_agg
)
WITH intersection_points AS (
SELECT identificador, st_collect(ct.geometria) AS geometria
FROM temp.via_rodov_limite_temp vrlt 
	JOIN temp.cutting_temp ct ON st_intersects(vrlt.geometria, ct.geometria)
GROUP BY identificador 
)
SELECT
	inicio_objeto,
	valor_tipo_limite,
	(st_dump(st_split(vrlt.geometria, sp.geometria))).geom AS geometria,
	seg_via_rodov_agg
FROM temp.via_rodov_limite_temp vrlt JOIN intersection_points AS sp ON vrlt.identificador = sp.identificador;

/* Apagar todos os elementos da tabela original e substituir por novos já unidos e
   e cortados nas junções com 3 ou mais linhas */

TRUNCATE TABLE public.via_rodov_limite CASCADE;

INSERT INTO public.via_rodov_limite (
	identificador,
	inicio_objeto,
	valor_tipo_limite,
	geometria)
SELECT
	identificador,
	inicio_objeto,
	valor_tipo_limite,
	geometria
FROM temp.via_rodov_limite_cortados;

/* Repor as ligações com as novas linhas */

INSERT INTO public.lig_segviarodov_viarodovlimite (via_rodov_limite_id, seg_via_rodov_id)
SELECT identificador AS via_rodov_limite_id, UNNEST(seg_via_rodov_agg)  AS seg_via_rodov_id
FROM temp.via_rodov_limite_cortados;

DROP SCHEMA IF EXISTS temp CASCADE;

END;