/*-- Consolidar linestrings da tabela segmentos via rodoviaria sempre que adjaentes
  (em X, Y e Z) e os seus attributos iguais. Por existirem atributos dependentes
  de ligações com outras tabelas, também essas ligações têm de ser acauteladas*/


/* Guardar camadas originais em backup */
CREATE SCHEMA IF NOT EXISTS backup;

CREATE TABLE backup.seg_via_rodov_bk (like public.seg_via_rodov);
INSERT INTO backup.seg_via_rodov_bk
SELECT * FROM public.seg_via_rodov;

CREATE TABLE backup.lig_valor_tipo_circulacao_seg_via_rodov_bk (like public.lig_valor_tipo_circulacao_seg_via_rodov);
INSERT INTO backup.lig_valor_tipo_circulacao_seg_via_rodov_bk
SELECT * FROM public.lig_valor_tipo_circulacao_seg_via_rodov;

CREATE TABLE backup.lig_segviarodov_viarodov_bk (like public.lig_segviarodov_viarodov);
INSERT INTO backup.lig_segviarodov_viarodov_bk
SELECT * FROM public.lig_segviarodov_viarodov;

CREATE TABLE backup.lig_segviarodov_viarodovlimite_bk (like public.lig_segviarodov_viarodovlimite);
INSERT INTO backup.lig_segviarodov_viarodovlimite_bk
SELECT * FROM public.lig_segviarodov_viarodovlimite;

/* Unir todas as linhas com atributos iguais, guardando em arrays as ligações a outras
   tabelas*/
CREATE SCHEMA IF NOT EXISTS temp;
CREATE TABLE temp.seg_via_rodov_temp (like public.seg_via_rodov INCLUDING DEFAULTS);

ALTER TABLE temp.seg_via_rodov_temp 
ADD COLUMN via_rodov_agg uuid[],
ADD COLUMN valor_tipo_circulacao_agg character varying[];

INSERT INTO temp.seg_via_rodov_temp (
    inicio_objeto,
	gestao,
	largura_via_rodov,
	multipla_faixa_rodagem,
	num_vias_transito,
	pavimentado,
	velocidade_max,
	jurisdicao,
	valor_caract_fisica_rodov,
	valor_estado_via_rodov,
	valor_posicao_vertical_transportes,
	valor_restricao_acesso,
	valor_sentido,
	valor_tipo_troco_rodoviario,
	geometria,
	via_rodov_agg,
	valor_tipo_circulacao_agg)
WITH via_rodov_agg AS
(SELECT lsv.seg_via_rodov_id , array_agg(DISTINCT lsv.via_rodov_id) AS via_rodov_agg
 FROM public.lig_segviarodov_viarodov lsv
 GROUP BY lsv.seg_via_rodov_id)
 , valor_tipo_circulacao_agg AS 
 (SELECT seg_via_rodov_id , array_agg(DISTINCT valor_tipo_circulacao_id) AS valor_tipo_circulacao_agg
 FROM public.lig_valor_tipo_circulacao_seg_via_rodov
 GROUP BY seg_via_rodov_id)
, multilines AS (
SELECT
	gestao,
	largura_via_rodov,
	multipla_faixa_rodagem,
	num_vias_transito,
	pavimentado,
	velocidade_max,
	jurisdicao,
	valor_caract_fisica_rodov,
	valor_estado_via_rodov,
	valor_posicao_vertical_transportes,
	valor_restricao_acesso,
	valor_sentido,
	valor_tipo_troco_rodoviario,
	st_collect(svr.geometria) AS geometria,
	via_rodov_agg,
	valor_tipo_circulacao_agg
FROM public.seg_via_rodov svr 
	LEFT JOIN via_rodov_agg vra ON (vra.seg_via_rodov_id = svr.identificador)
	LEFT JOIN valor_tipo_circulacao_agg vtca ON (vtca.seg_via_rodov_id = svr.identificador)
GROUP BY
	gestao,
	largura_via_rodov,
	multipla_faixa_rodagem,
	num_vias_transito,
	pavimentado,
	velocidade_max,
	jurisdicao,
	valor_caract_fisica_rodov,
	valor_estado_via_rodov,
	valor_posicao_vertical_transportes,
	valor_restricao_acesso,
	valor_sentido,
	valor_tipo_troco_rodoviario,
	via_rodov_agg,
	valor_tipo_circulacao_agg	
	)
SELECT 
	now(),
	gestao,
	largura_via_rodov,
	multipla_faixa_rodagem,
	num_vias_transito,
	pavimentado,
	velocidade_max,
	jurisdicao,
	valor_caract_fisica_rodov,
	valor_estado_via_rodov,
	valor_posicao_vertical_transportes,
	valor_restricao_acesso,
	valor_sentido,
	valor_tipo_troco_rodoviario,
	(ST_DUMP(st_linemerge(geometria))).geom AS geometria,
	via_rodov_agg,
	valor_tipo_circulacao_agg	
FROM multilines;

CREATE INDEX ON temp.seg_via_rodov_temp (identificador);
CREATE INDEX ON temp.seg_via_rodov_temp USING gist(geometria);

/*-- Reunir pontos de intersecção entre linhas para cortar entroncamentos e cruzamentos 
	ao mesmo nível */

DROP TABLE IF EXISTS temp.cutting_temp;

CREATE TABLE temp.cutting_temp as
	SELECT 
		(st_dump(st_collect(st_endpoint(geometria),st_startpoint(geometria)))).geom AS geometria,
		valor_posicao_vertical_transportes
	FROM temp.seg_via_rodov_temp
	UNION ALL
	SELECT (st_dump(st_intersection(svrt1.geometria, svrt2.geometria))).geom AS geometria,
	svrt1.valor_posicao_vertical_transportes
	FROM temp.seg_via_rodov_temp AS svrt1
	JOIN temp.seg_via_rodov_temp AS svrt2
	ON (svrt1.identificador > svrt2.identificador) AND st_crosses(svrt1.geometria,svrt2.geometria) AND svrt1.valor_posicao_vertical_transportes = svrt2.valor_posicao_vertical_transportes;

CREATE INDEX ON  temp.cutting_temp USING GIST(geometria);

/* cortar linhas previamente unidas com os pontos de corte */

CREATE TABLE temp.seg_via_rodov_cortados (like temp.seg_via_rodov_temp INCLUDING DEFAULTS);

INSERT INTO temp.seg_via_rodov_cortados (
	inicio_objeto,
	gestao,
	largura_via_rodov,
	multipla_faixa_rodagem,
	num_vias_transito,
	pavimentado,
	velocidade_max,
	jurisdicao,
	valor_caract_fisica_rodov,
	valor_estado_via_rodov,
	valor_posicao_vertical_transportes,
	valor_restricao_acesso,
	valor_sentido,
	valor_tipo_troco_rodoviario,
	geometria,
	via_rodov_agg,
	valor_tipo_circulacao_agg
)
WITH intersection_points AS (
SELECT identificador, st_collect(ct.geometria) AS geometria
FROM temp.seg_via_rodov_temp svrt 
	JOIN temp.cutting_temp ct ON st_intersects(svrt.geometria, ct.geometria)
		AND ct.valor_posicao_vertical_transportes = svrt.valor_posicao_vertical_transportes
GROUP BY identificador 
)
SELECT
	inicio_objeto,
	gestao,
	largura_via_rodov,
	multipla_faixa_rodagem,
	num_vias_transito,
	pavimentado,
	velocidade_max,
	jurisdicao,
	valor_caract_fisica_rodov,
	valor_estado_via_rodov,
	valor_posicao_vertical_transportes,
	valor_restricao_acesso,
	valor_sentido,
	valor_tipo_troco_rodoviario,
	(st_dump(st_split(svrt.geometria, sp.geometria))).geom AS geometria,
	via_rodov_agg,
	valor_tipo_circulacao_agg
FROM temp.seg_via_rodov_temp svrt JOIN intersection_points AS sp ON svrt.identificador = sp.identificador;

/* Apagar todos os elementos da tabela original e substituir por novos já unidos e
   e cortados nas junções com 3 ou mais linhas */

TRUNCATE TABLE public.seg_via_rodov CASCADE;

INSERT INTO public.seg_via_rodov (
	identificador,
	inicio_objeto,
	gestao,
	largura_via_rodov,
	multipla_faixa_rodagem,
	num_vias_transito,
	pavimentado,
	velocidade_max,
	jurisdicao,
	valor_caract_fisica_rodov,
	valor_estado_via_rodov,
	valor_posicao_vertical_transportes,
	valor_restricao_acesso,
	valor_sentido,
	valor_tipo_troco_rodoviario,
	geometria)
SELECT
	identificador,
	inicio_objeto,
	gestao,
	largura_via_rodov,
	multipla_faixa_rodagem,
	num_vias_transito,
	pavimentado,
	velocidade_max,
	jurisdicao,
	valor_caract_fisica_rodov,
	valor_estado_via_rodov,
	valor_posicao_vertical_transportes,
	valor_restricao_acesso,
	valor_sentido,
	valor_tipo_troco_rodoviario,
	geometria
FROM temp.seg_via_rodov_cortados;

/* Repor as ligações com as novas linhas */

INSERT INTO public.lig_segviarodov_viarodov (seg_via_rodov_id, via_rodov_id)
SELECT identificador AS seg_via_rodov_id, UNNEST(via_rodov_agg)  AS via_rodov_id
FROM temp.seg_via_rodov_cortados;

INSERT INTO public.lig_valor_tipo_circulacao_seg_via_rodov (seg_via_rodov_id, valor_tipo_circulacao_id)
SELECT identificador AS seg_via_rodov_id, UNNEST(valor_tipo_circulacao_agg)  AS valor_tipo_circulacao_id
FROM temp.seg_via_rodov_cortados;

DROP SCHEMA IF EXISTS temp CASCADE;