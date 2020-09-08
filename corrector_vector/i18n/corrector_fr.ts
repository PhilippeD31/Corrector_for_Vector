<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="fr_FR" sourcelanguage="en_US">
<context>
    <name>CorrectorVector</name>
    <message>
        <location filename="../ui_corrector_vector.ui" line="23"/>
        <source>Corrector for Vector</source>
        <translation>Correcteur pour Vecteur</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="34"/>
        <source>Source layer to correct or deform</source>
        <translation>La couche source à corriger ou déformer</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="52"/>
        <source>Only selected</source>
        <translation>Seulement la sélection</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="67"/>
        <source>In order to deform the source layer, the plugin will use a layer of simple oriented linestrings (arrows) that define distortion vectors.
For a simple translation, only one arrow is needed. For more complex twists, draw more arrows throughout the source layer.
Draw an arrow with only 2 vertices, from a point of the source layer to the position it will be moved to.
Tip: in order to anchor an area that is not to be moved, you add a zero length arrow (its end point at the same position as its start point).</source>
        <translation>Afin de déformer les polygones de la source, cette extension utilise une couche de lignes simples et orientées (des flèches) qui définissent les vecteurs de déformation. Dessiner dans la couche des flèches autant de lignes que nécessaire.
Tracer des flèches avec seulement 2 sommets. Leur point de départ : un point de la couche source. Leur point d&apos;arrivée : la position à laquelle ce point se retrouvera après le traitement.
Astuce : pour fixer une zone qui ne doit pas être déplacée, il faut ajouter une flèche de longueur nulle (son point d&apos;arrivée à la même position que son point de départ).</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="77"/>
        <source>Layer with linestrings : deformation vectors (arrows)</source>
        <translation>La couche avec les lignes vecteurs de déformation (flèches)</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="102"/>
        <source>Create temp layer and draw</source>
        <translation>Créer couche temp et dessiner</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="171"/>
        <source>Process with PostgreSQL / PostGIS (faster)</source>
        <translation>Traiter avec PostgreSQL / PostGIS (plus rapide)</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="194"/>
        <source>Connection (PostGIS 2.x minimum)</source>
        <translation>Connexion (PostGIS 2.x minimum)</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="209"/>
        <source>select working postgres connection</source>
        <translation>Choisir la connexion Postgres</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="216"/>
        <source>Refresh</source>
        <translation>Rafraichir</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="228"/>
        <source>Choose the working schema (temp tables will be created)</source>
        <translation>Choisir le schéma de travail (des tables temp seront créées)</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="274"/>
        <source>Add a new schema</source>
        <translation>Nouveau schéma</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="556"/>
        <source>Start</source>
        <translation>Démarrer</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="745"/>
        <source>informations</source>
        <translation>informations</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="507"/>
        <source>Without PostGIS</source>
        <translation>Sans PostGIS</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="773"/>
        <source>Log</source>
        <translation>Journal</translation>
    </message>
    <message>
        <location filename="../ui_corrector_vector.ui" line="730"/>
        <source>informations during the process</source>
        <translation>informations pendant le processus</translation>
    </message>
</context>
<context>
    <name>plugin</name>
    <message>
        <location filename="../corrector_vector.py" line="550"/>
        <source>Important!</source>
        <translation>Attention !</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="162"/>
        <source>Please choose the source layer to deform.</source>
        <translation>Il faut choisir la couche source à déformer.</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="172"/>
        <source>The CRS of the source layer is undefined or it doesn&apos;t have an EPSG number. Please, define the CRS of that layer with an ESPG ID.</source>
        <translation>Le SCR de la couche source n&apos;est pas défini ou il n&apos;a pas de numéro EPSG. Il faut définir le SCR de la couche avec un code EPSG.</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="178"/>
        <source>Please choose (or create) the layer with deformation vectors (arrows).</source>
        <translation>Il faut choisir (ou créer) la couche avec les vecteurs de déformation (flèches).</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="255"/>
        <source>Couldn&apos;t create temporary layer with [%s]. Process failed.</source>
        <translation>Echec de la création de la couche temporaire à partir de [%s].</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="265"/>
        <source>Prepare layer with deformations from your arrows: step 1</source>
        <translation>Je prépare la couche des déform à partir des &quot;flèches&quot;</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="345"/>
        <source>Exploding your polygons to points</source>
        <translation>Décomposer les polygones en points</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="381"/>
        <source>Preparing 2 triangulation layers from step 1</source>
        <translation>Préparer 2 couche de triangulation</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="422"/>
        <source>Moving each point</source>
        <translation>Déplacer chaque point</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="425"/>
        <source>Failed to import &apos;tpointsdepla&apos; into Spatialite.</source>
        <translation>Echec de l&apos;import de &apos;tpointsdepla&apos; dans Spatialite.</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="616"/>
        <source>End</source>
        <translation>Fin</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="653"/>
        <source>Error importing into PostGIS
{0}</source>
        <translation>Erreur lors de l&apos;import dans PostGIS
{0}</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="54"/>
        <source>Correct, deform a polygon layer</source>
        <translation>Corriger, déformer une couche  polygone</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="58"/>
        <source>Corrector for Vector</source>
        <translation>Correcteur pour Vecteur</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="130"/>
        <source>Please choose first the source layer to deform.</source>
        <translation>Il faut d&apos;abord choisir la couche source à déformer.</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="154"/>
        <source>Layer created : </source>
        <translation>Couche créée : </translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="154"/>
        <source>Draw your deformation arrows in the temp layer [{0}] and save the layer before starting the treatment.</source>
        <translation>Dessiner vos flèches de déformations dans la couche temp [{0}] et enregistrer les modifications avant de démarrer le traitement.</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="396"/>
        <source>The process failed at triangulation (TINinterpolation).</source>
        <translation>Le traitement a échoué pendant la triangulation (TINinterpolation).</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="446"/>
        <source>Rebuild the polygons with the points that were moved</source>
        <translation>Reconstruc. des polygones aves les points déplacés</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="616"/>
        <source>You may inspect the objects in the layer &quot;corrected&quot;.
If they are not okay, you can move your arrows or add new ones, and restart the process.</source>
        <translation>Vous pouvez inspecter les objets dans la couche &quot;corrected&quot;.
S&apos;ils ne sont pas satisfaisants, vous pouvez déplacer vos flèches ou en créer de nouvelles, puis redémarrer le traitement.</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="494"/>
        <source>Import into spatialite failed.
{0}</source>
        <translation>Echec de l&apos;import dans spatialite.
{0}</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="509"/>
        <source>Export to spatialite failed.
{0}</source>
        <translation>Echec de l&apos;import dans spatialite.
{0}</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="514"/>
        <source>Process failed:
SQL error:
</source>
        <translation>Echec du traitement :
Erreur SQL :
</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="539"/>
        <source>Please choose the PostGIS connection.</source>
        <translation>Il faut choisir la connexion PostGIS.</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="550"/>
        <source>Please choose the working schema.</source>
        <translation>Il faut choisir le schéma de travail.</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="562"/>
        <source>Importing the layers into PostGIS...</source>
        <translation>Importation des couches dans PostGIS...</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="570"/>
        <source>Problem!</source>
        <translation>Problème !</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="570"/>
        <source>Failed to import layer %s into Postgis.
Please check your rights in that schema.</source>
        <translation>Echec de l&apos;import dans Postgis.
Veuillez vérifier les droits d&apos;écriture dans ce schéma.</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="574"/>
        <source>PostGIS processing : please wait...</source>
        <translation>Traitement sous PostGIS : veuillez patienter...</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="597"/>
        <source>The SQL script was frozen and had to be terminated. See the Log tab below</source>
        <translation>Le script SQL était bloqué et a dû être terminé. Voir l&apos;onglet Journal ci-dessous</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="604"/>
        <source>SQL error. See the Log tab below</source>
        <translation>Erreur SQL. Voir l&apos;onglet Journal ci-dessous</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="144"/>
        <source>arrows</source>
        <comment>layer name</comment>
        <translation>flèches</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="186"/>
        <source>The layer with deformation vectors (arrows) is empty. Please draw the arrows first.</source>
        <translation>La couche avec les lignes de déformation (flèches) est vide. Il faut dessiner les flèches d&apos;abord.</translation>
    </message>
    <message>
        <location filename="../corrector_vector.py" line="607"/>
        <source>The end</source>
        <translation>Fin</translation>
    </message>
</context>
</TS>
