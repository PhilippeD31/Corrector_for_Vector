-- On a NEWLAYER : une couche de polygones qu'il faut recaler
-- et FLECHES : la couche des flèches de recalage

-- SCHEM, EPSG, NEWLAYER, IDPK et FLECHES doivent etre passes en parametre de psql : --set=SCHEM=leschema

\set ON_ERROR_STOP on

\echo ### Creer couche de points de recalage, base pour les triangles de Delauney,
--  ils vont entourer grille et accueillir les vecteurs (conv en points) :
DROP TABLE IF EXISTS :SCHEM.trecal ;
CREATE TABLE :SCHEM.trecal ( uid serial PRIMARY KEY, deltax real, deltay real, geom geometry(POINT,:EPSG) ) ;
WITH circ AS (
  SELECT ST_MinimumBoundingCircle( ST_Collect(ST_Buffer(geom,1000)), 8) g1  FROM :NEWLAYER ),
dd as ( select ST_DumpPoints(g1) AS gdump from circ )
INSERT INTO :SCHEM.trecal (geom)  SELECT (gdump).geom geom  FROM dd ;
-- Retirer le 1er pt di cercle qui est en doublon avec le dernier :
DELETE FROM :SCHEM.trecal WHERE uid=1 ;

-- Ajouter les vecteurs de recalage convertis en points avec les infos de décalage x et y :
INSERT INTO :SCHEM.trecal (deltax, deltay, geom)  SELECT
	ST_X(ST_EndPoint(v.geom))-ST_X(ST_StartPoint(v.geom)) deltax,
	ST_Y(ST_EndPoint(v.geom))-ST_Y(ST_StartPoint(v.geom)) deltay,
	ST_StartPoint(v.geom) geom
 FROM :FLECHES v 	;

\echo ### Créer des triangles de Delauney à partir des trecal :
DROP TABLE IF EXISTS :SCHEM.tdelauney ;
CREATE TABLE :SCHEM.tdelauney ( uid serial PRIMARY KEY, geom geometry(POLYGON,:EPSG) ) ;
WITH dd AS ( SELECT ST_DelaunayTriangles( ST_Collect(geom) ) g1 FROM :SCHEM.trecal )
INSERT INTO :SCHEM.tdelauney (geom) SELECT (ST_Dump(g1)).geom geom FROM dd ;

\echo ### Recréer le lien entre les pts de trecal et les triangles de tdelauney :
DROP TABLE IF EXISTS :SCHEM.trecal_tdelauney ;
CREATE TABLE :SCHEM.trecal_tdelauney AS
 SELECT r.uid idpt, d.uid iddel, deltax, deltay, r.geom::geometry(POINT,:EPSG) geom
  FROM :SCHEM.trecal r, :SCHEM.tdelauney d WHERE ST_Touches(r.geom,d.geom) ;



\echo ### Chercher à attribuer deltax et y proportionnels aux pts trecal qui n en ont pas encore :
WITH nu AS ( SELECT idpt idnu, iddel idtri, geom g1 FROM :SCHEM.trecal_tdelauney WHERE deltax IS NULL ),
dd AS (
 SELECT DISTINCT ON (idpt,idnu) idpt idval, idnu, deltax x, deltay y, geom, ST_Distance(g1,geom) dist
  FROM nu, :SCHEM.trecal_tdelauney
  WHERE deltax IS NOT NULL    -- AND iddel=idtri AND idpt<>idnu
),
agg AS ( SELECT idnu, count(*) nb, array_agg(dist ORDER BY dist) dd, array_agg(geom ORDER BY dist) gg,
 array_agg(x ORDER BY dist) xx, array_agg(y ORDER BY dist) yy
 FROM dd  GROUP BY idnu 
),
compar AS ( SELECT idnu, xx , yy, dd,
 CASE 
  WHEN xx[1]=xx[2] THEN xx[1]
	WHEN dd[1]=dd[2] THEN (xx[1]+xx[2])/2  -- équidistance donc a applique la moyenne
	-- on a forcément dd[1]<dd[2] à cause du ORDER BY dist : idnu est plus proche de g1
	  -- angle droit entre A et B :  diag²=A²+B²  ; dd[2] est la diagonale :
		--  chercher si l'angle suivant dépasse 90°: entre dd[1] et la ligne gg[1]-gg[2]
		-- si diag²>=d1²+d2² alors appliquer la valeur xx[1]
	WHEN power(dd[2],2) >= power(dd[1],2) + power(ST_Distance(gg[1],gg[2]),2) THEN xx[1]
	  -- x2=x1+diff ;   (x1+x1+diff)/2 = x1 + diff*0.5
	   -- à angle droit on a diff=0  et  d2²=d1²+dist(g1-g2)²  donc  d1²+dist(g1-g2)²-d2² = 0
		 -- à équidistance on a diff=0.5  et  d1²=d2²  donc 0.5 * d1²+dist(g1-g2)²-d2² / dist(g1-g2)² = 0.5
	  -- d1²=d2²+F ; F=d1²-d2² ; 90°: F=dist(g1-g2)²  ;  équidistance: F=0
		-- V= x1+diff*N  ;  90°: N=0  ;  équidistance: N=0.5
		-- d1²-d2² / dist(g1-g2)² * 0.5 = diff  ;  x1 = x2-diff  ; V= x1 + (x2-x1)*diff
	ELSE xx[1] + (xx[2]-xx[1]) * 0.5 * (power(dd[1],2)+power(ST_Distance(gg[1],gg[2]),2)-power(dd[2],2)) / power(ST_Distance(gg[1],gg[2]),2)
 END newx ,
 CASE 
  WHEN yy[1]=yy[2] THEN yy[1]
	WHEN dd[1]=dd[2] THEN (yy[1]+yy[2])/2  -- équidistance donc a applique la moyenne
	-- on a forcément dd[1]<dd[2] à cause du ORDER BY dist : idnu est plus proche de g1
	WHEN power(dd[2],2) >= power(dd[1],2) + power(ST_Distance(gg[1],gg[2]),2) THEN yy[1]
	ELSE yy[1] + (yy[2]-yy[1]) * 0.5 * (power(dd[1],2)+power(ST_Distance(gg[1],gg[2]),2)-power(dd[2],2)) / power(ST_Distance(gg[1],gg[2]),2)
 END newy
 FROM agg 
)
UPDATE :SCHEM.trecal SET deltax=newx , deltay=newy  FROM compar  WHERE uid=idnu ;


\echo ### Créer des triangles de Delauney 3D pour deltax à partir des trecal élevés à deltax :
DROP TABLE IF EXISTS :SCHEM.tdelauney3dx ;
CREATE TABLE :SCHEM.tdelauney3dx ( uid serial PRIMARY KEY, geom geometry(POLYGONZ,:EPSG) ) ;
WITH p3d AS ( SELECT ST_Translate(ST_Force3D(geom),0,0,deltax) geom FROM :SCHEM.trecal ),
dd AS ( SELECT ST_DelaunayTriangles( ST_Collect(geom) ) g1 FROM p3d )
INSERT INTO :SCHEM.tdelauney3dx (geom) SELECT (ST_Dump(g1)).geom geom FROM dd ;
\echo ### Créer des triangles de Delauney 3D pour deltay à partir des trecal élevés à deltay :
DROP TABLE IF EXISTS :SCHEM.tdelauney3dy ;
CREATE TABLE :SCHEM.tdelauney3dy ( uid serial PRIMARY KEY, geom geometry(POLYGONZ,:EPSG) ) ;
WITH p3d AS ( SELECT ST_Translate(ST_Force3D(geom),0,0,deltay) geom FROM :SCHEM.trecal ),
dd AS ( SELECT ST_DelaunayTriangles( ST_Collect(geom) ) g1 FROM p3d )
INSERT INTO :SCHEM.tdelauney3dy (geom) SELECT (ST_Dump(g1)).geom geom FROM dd ;


-- #########################  FIN de la préparation  #########################


\echo ### Exploser polygones de NEWLAYER en points :
DROP TABLE IF EXISTS :SCHEM.tpoints ;
CREATE TABLE :SCHEM.tpoints ( uid serial PRIMARY KEY, idg integer, deltax real, deltay real,
 path integer[],  geom geometry(POINTZ,:EPSG) ) ;
--CREATE TABLE :SCHEM.tpoints AS
WITH ee AS ( SELECT :IDPK, ST_DumpPoints(ST_Multi(geom)) AS gdump FROM :NEWLAYER )
INSERT INTO :SCHEM.tpoints ( idg, path, geom )
  SELECT :IDPK idg, (gdump).path path, ST_Force3D((gdump).geom)::geometry(POINTZ,:EPSG) geom  FROM ee ;


\echo ### Intersecter tdelauney3dx et points pour interpoler la valeur deltaX de chacun :
-- Creer des lignes verticales pour chaque tpoints de la grille 
WITH ll AS ( SELECT idg id, path p,
  ST_MakeLine(ST_Translate(geom,0,0,-1000000), ST_Translate(geom,0,0,1000000) )::geometry(LINESTRINGZ,:EPSG) g1
  FROM :SCHEM.tpoints ),
inter AS ( SELECT DISTINCT ON (id,p) id, p, ST_Z(ST_3DIntersection(g1,geom)) zz
	FROM ll, :SCHEM.tdelauney3dx  WHERE ST_3DIntersects(g1,geom) )
UPDATE :SCHEM.tpoints SET deltax=zz  FROM inter  WHERE idg=id  AND  path=p ;


\echo ### Intersecter tdelauney3dy et points pour interpoler leur valeur deltaY :
WITH ll AS ( SELECT idg id, path p,
  ST_MakeLine(ST_Translate(geom,0,0,-1000000), ST_Translate(geom,0,0,1000000) )::geometry(LINESTRINGZ,:EPSG) g1
  FROM :SCHEM.tpoints ),
inter AS ( SELECT DISTINCT ON (id,p) id, p, ST_Z(ST_3DIntersection(g1,geom)) zz
	FROM ll, :SCHEM.tdelauney3dy  WHERE ST_3DIntersects(g1,geom) )
UPDATE :SCHEM.tpoints SET deltay=zz  FROM inter  WHERE idg=id  AND  path=p ;

\echo ### Déplacer les point de tpoints par deltax et y :
DROP TABLE IF EXISTS :SCHEM.tpointsdepla ;
CREATE TABLE :SCHEM.tpointsdepla AS
  SELECT uid, idg, path, ST_Translate(ST_Force2D(geom),deltax,deltay)::geometry(POINT,:EPSG) geom
   FROM :SCHEM.tpoints ;


\echo ### Reassembler les points deplaces en anneaux (rings) :
DROP TABLE IF EXISTS :SCHEM.trings ;
CREATE TABLE :SCHEM.trings AS
WITH gr1 AS (  SELECT idg, path[1] p1, path[2] p2, array_agg(geom ORDER BY path) as pts
	FROM :SCHEM.tpointsdepla  GROUP BY idg, path[1], path[2]  )
SELECT idg, p1, p2, ST_IsRing(ST_MakeLine(pts)) ringvalid,
	ST_MakeLine(pts)::geometry(LINESTRING,:EPSG) geom  FROM gr1 ;


\echo ### Reassembler les anneaux en polygones (anneaux externes et internes) :
WITH grext AS ( SELECT idg, p1, geom exter FROM :SCHEM.trings  WHERE p2=1 AND ringvalid )
,grint AS ( SELECT idg, p1, array_agg(geom) inter FROM :SCHEM.trings
  WHERE p2>1 AND ringvalid  GROUP BY idg, p1  )
,monos AS ( SELECT grext.idg,
		CASE WHEN inter IS NULL THEN ST_MakePolygon(exter)
		ELSE ST_MakePolygon( exter, inter )
		END geom  FROM grext
	LEFT JOIN grint  ON grext.idg = grint.idg  AND  grext.p1 = grint.p1 )
,multis AS ( SELECT idg, ST_Multi( ST_Collect(geom) ) g3 FROM monos  GROUP BY idg )
UPDATE :NEWLAYER SET geom= g3  FROM multis m  WHERE :NEWLAYER.:IDPK = m.idg ;



/*
WITH gr1 AS (  SELECT idg, path[1] p1, path[2] p2, array_agg(geom ORDER BY path) as pts
	FROM :SCHEM.tpointsdepla  GROUP BY idg, path[1], path[2]  )
,grext AS ( SELECT idg, p1, p2, ST_MakeLine(pts) exter  FROM gr1  WHERE p2=1  )
,grint AS ( SELECT idg, p1, p2, array_agg(ST_MakeLine(pts)) inter FROM gr1  WHERE p2>1  GROUP BY idg, p1, p2  )
,monos AS ( SELECT grext.idg,
		CASE WHEN inter IS NULL THEN ST_MakePolygon(exter)::geometry(POLYGON,:EPSG)
		ELSE ST_MakePolygon( exter, inter )::geometry(POLYGON,:EPSG)
		END geom  FROM grext
	LEFT JOIN grint  ON grext.idg = grint.idg  AND  grext.p1 = grint.p1 )
,multis AS ( SELECT idg, ST_Multi( ST_Collect(geom) ) g3 FROM monos  GROUP BY idg )
UPDATE :NEWLAYER SET geom= g3  FROM multis m  WHERE :NEWLAYER.:IDPK = m.idg ;
*/

/* \echo ### TEST reassembler les outer-rings (anneaux ext) sans assembler les multi polygones :
DROP TABLE IF EXISTS :SCHEM.tpolysimples ;
CREATE TABLE :SCHEM.tpolysimples AS
 WITH gr1 AS (  SELECT idg, path[1] p1, path[2] p2, array_agg(geom ORDER BY path) as pts
  FROM :SCHEM.tpointsdepla  GROUP BY idg, path[1], path[2]  )
 , grext AS (  SELECT idg, p1, p2, ST_MakeLine(pts) exter  FROM gr1  WHERE p2=1  )
 SELECT idg, p1, p2, ST_MakePolygon(exter)::geometry(POLYGON,:EPSG) geom  FROM grext ; */

