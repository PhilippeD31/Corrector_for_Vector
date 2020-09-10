# Corrector for Vector
**A plugin for QGIS**  
Designed to correct, move and repair polygons that have been improperly digitized (or digitized on a bad map) and that exhibit offsets and distortions.  
In order to deform the polygons, the plugin uses a layer of simple oriented linestrings (arrows) : the deformation vectors. In the linestrings layer, you simply draw as many deformation arrows as needed.  
And choose to process it either with or without PostGIS (faster with PostGIS).

**FR : une extension pour QGIS**  
Ce nouveau plugin "Correcteur pour Vecteur" a été conçu pour recaler, déplacer et réparer des polygones qui ont été mal numérisés (ou numérisés sur un mauvais référentiel) et qui présentent des décalages et déformations.  
Afin de déformer les polygones, cette extension utilise une couche de lignes simples et orientées (des flèches) qui définissent les vecteurs de déformation. Dans la couche de lignes, dessiner autant de flèches que nécessaire. Tracer des flèches avec seulement 2 sommets. Leur point de départ : un point de la couche source. Leur point d'arrivée : la position à laquelle ce point se retrouvera après le traitement.  
On pourra choisir de faire le traitement avec ou sans PostGIS. C'est plus rapide avec PostGIS.

Pour un test rapide, on trouvera 2 couches prêtes à l'emploi dans le dossier *testing*.
