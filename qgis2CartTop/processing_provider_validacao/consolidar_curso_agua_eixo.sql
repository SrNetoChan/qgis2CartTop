/*-- Consolidar linestrings da tabela curso de água eixo sempre que adjaentes
  (em X, Y e Z) e os seus attributos iguais. */

/* Guardar camadas originais em backup */
CREATE SCHEMA IF NOT EXISTS backup;

CREATE TABLE backup.curso_de_agua_eixo_bk (like public.curso_de_agua_eixo);
INSERT INTO backup.curso_de_agua_eixo_bk
SELECT * FROM public.curso_de_agua_eixo;

BEGIN;

/* Unir todas as linhas com atributos iguais, guardando em arrays as ligações a outras
   tabelas*/
CREATE SCHEMA IF NOT EXISTS temp;
CREATE TABLE temp.curso_de_agua_eixo_temp (like public.curso_de_agua_eixo INCLUDING DEFAULTS);

INSERT INTO temp.curso_de_agua_eixo_temp (
    inicio_objeto,
		nome,
		comprimento,
		delimitacao_conhecida,
		ficticio,
		largura,
		id_hidrografico,
		id_curso_de_agua_area,
		ordem_hidrologica,
		origem_natural,
		valor_curso_de_agua,
		valor_persistencia_hidrologica,
		valor_posicao_vertical,
		geometria)
WITH multilines AS (
SELECT
	nome,
	comprimento,
	delimitacao_conhecida,
	ficticio,
	largura,
	id_hidrografico,
	id_curso_de_agua_area,
	ordem_hidrologica,
	origem_natural,
	valor_curso_de_agua,
	valor_persistencia_hidrologica,
	valor_posicao_vertical,
	ST_COLLECT(geometria) AS geometria
FROM public.curso_de_agua_eixo cae 
GROUP BY
	nome,
	comprimento,
	delimitacao_conhecida,
	ficticio,
	largura,
	id_hidrografico,
	id_curso_de_agua_area,
	ordem_hidrologica,
	origem_natural,
	valor_curso_de_agua,
	valor_persistencia_hidrologica,
	valor_posicao_vertical
)
SELECT 
	now(),
	nome,
	comprimento,
	delimitacao_conhecida,
	ficticio,
	largura,
	id_hidrografico,
	id_curso_de_agua_area,
	ordem_hidrologica,
	origem_natural,
	valor_curso_de_agua,
	valor_persistencia_hidrologica,
	valor_posicao_vertical,
	(ST_DUMP(st_linemerge(geometria))).geom AS geometria
FROM multilines;

CREATE INDEX ON temp.curso_de_agua_eixo_temp (identificador);
CREATE INDEX ON temp.curso_de_agua_eixo_temp USING gist(geometria);

/*-- Reunir pontos de intersecção entre linhas para cortar entroncamentos e cruzamentos 
	ao mesmo nível */

DROP TABLE IF EXISTS temp.cutting_temp;

CREATE TABLE temp.cutting_temp as
	SELECT 
		(st_dump(st_collect(st_endpoint(geometria),st_startpoint(geometria)))).geom AS geometria 
	FROM temp.curso_de_agua_eixo_temp
	UNION ALL
	SELECT (st_dump(st_intersection(caet1.geometria, caet2.geometria))).geom AS geometria
	FROM temp.curso_de_agua_eixo_temp AS caet1
	JOIN temp.curso_de_agua_eixo_temp AS caet2
	ON (caet1.identificador > caet2.identificador) AND st_crosses(caet1.geometria,caet2.geometria) AND caet1.valor_posicao_vertical = caet2.valor_posicao_vertical;

CREATE INDEX ON  temp.cutting_temp USING GIST(geometria);

/* cortar linhas previamente unidas com os pontos de corte */

CREATE TABLE temp.curso_de_agua_eixo_cortados (like temp.curso_de_agua_eixo_temp INCLUDING DEFAULTS);

INSERT INTO temp.curso_de_agua_eixo_cortados (
	inicio_objeto,
	nome,
	comprimento,
	delimitacao_conhecida,
	ficticio,
	largura,
	id_hidrografico,
	id_curso_de_agua_area,
	ordem_hidrologica,
	origem_natural,
	valor_curso_de_agua,
	valor_persistencia_hidrologica,
	valor_posicao_vertical,
	geometria
)
WITH intersection_points AS (
SELECT identificador, st_collect(ct.geometria) AS geometria
FROM temp.curso_de_agua_eixo_temp caet 
	JOIN temp.cutting_temp ct ON st_intersects(caet.geometria, ct.geometria)
GROUP BY identificador 
)
SELECT
	inicio_objeto,
	nome,
	comprimento,
	delimitacao_conhecida,
	ficticio,
	largura,
	id_hidrografico,
	id_curso_de_agua_area,
	ordem_hidrologica,
	origem_natural,
	valor_curso_de_agua,
	valor_persistencia_hidrologica,
	valor_posicao_vertical,	
	(st_dump(st_split(caet.geometria, sp.geometria))).geom AS geometria
FROM temp.curso_de_agua_eixo_temp caet JOIN intersection_points AS sp ON caet.identificador = sp.identificador;

/* Apagar todos os elementos da tabela original e substituir por novos já unidos e
   e cortados nas junções com 3 ou mais linhas */

TRUNCATE TABLE public.curso_de_agua_eixo CASCADE;

INSERT INTO public.curso_de_agua_eixo (
	inicio_objeto,
	nome,
	comprimento,
	delimitacao_conhecida,
	ficticio,
	largura,
	id_hidrografico,
	id_curso_de_agua_area,
	ordem_hidrologica,
	origem_natural,
	valor_curso_de_agua,
	valor_persistencia_hidrologica,
	valor_posicao_vertical,
	geometria)
SELECT
	inicio_objeto,
	nome,
	comprimento,
	delimitacao_conhecida,
	ficticio,
	largura,
	id_hidrografico,
	id_curso_de_agua_area,
	ordem_hidrologica,
	origem_natural,
	valor_curso_de_agua,
	valor_persistencia_hidrologica,
	valor_posicao_vertical,	
	geometria
FROM temp.curso_de_agua_eixo_cortados;

DROP SCHEMA IF EXISTS temp CASCADE;

END;