# -*- coding: utf-8 -*-
"""***************************************************************************
    copyright            : Philippe Desboeufs
    begin                : 2020-06-12
   ***************************************************************************
   *   This program is free software; you can redistribute it and/or modify  *
   *   it under the terms of the GNU General Public License as published by  *
   *   the Free Software Foundation; either version 2 of the License, or     *
   *   (at your option) any later version.                                   *
   ************************************************************************"""
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtSql import *
from qgis.PyQt import uic
from qgis.core import *
from qgis.gui import *
import os, time, sys
from qgis.utils import iface, spatialite_connect
from qgis import processing
import subprocess
import tempfile

#from .TableSet import tableSet
from .PSQL import PSQL


class plugin:
  def __init__(self, iface):
    self.plugin_dir= os.path.dirname(__file__)
    self.PQBdockwidget= None
    self.params= "PluginCorrectorVector/" # User Param in QSettings

  def tr(self, txt, disambiguation=None):
    return QCoreApplication.translate('plugin', txt, disambiguation)

  def initGui(self):
    pluginPath= os.path.abspath(os.path.dirname(__file__))
    # Translator :
    overrideLocale= QSettings().value("locale/overrideFlag", False, type=bool)
    if not overrideLocale:  localeFullName= QLocale.system().name()
    else:
      localeFullName= QSettings().value("locale/userLocale", "")
      if localeFullName.__class__.__name__=='QVariant': localeFullName= 'en_EN'
    localePath= pluginPath + os.sep +"i18n"+ os.sep +"corrector_" + localeFullName[0:2] + ".qm"
    if not QFileInfo(localePath).exists(): # If no corrector_ll.qm, looking for corrector_ll_CC.qm
      localePath = pluginPath + os.sep +"i18n"+ os.sep +"corrector_" + localeFullName + ".qm"
    if QFileInfo(localePath).exists():
      self.translator = QTranslator()
      self.translator.load(localePath)
      QCoreApplication.installTranslator(self.translator)
    
    icone= pluginPath + os.sep +"icon.png"
    self.aCorrector= QAction( QIcon(icone), self.tr("Correct, deform a polygon layer"), iface.mainWindow() ) # Géoréférencer, recaler, déformer une couche de polygones
    self.aCorrector.triggered.connect(self.show)
    iface.addToolBarIcon(self.aCorrector)
    
    self.nomDuMenu= self.tr("Corrector for Vector")
    iface.addPluginToVectorMenu(self.nomDuMenu, self.aCorrector)

  def unload(self):
    try:  #if self.PQBdockwidget: # hide the widget
      self.PQBdockwidget.hide()
      iface.removeDockWidget(self.PQBdockwidget)
      self.PQBdockwidget.deleteLater()
    except: pass
    iface.removeToolBarIcon(self.aCorrector)
    iface.removePluginVectorMenu(self.nomDuMenu, self.aCorrector)


  def eventsConnect(self): 
    self.dlg.bTempArrows.clicked.connect(self.createTempArrows)
    self.dlg.bStart.clicked.connect(self.processSpatialite)
    self.dlg.bStartPG.clicked.connect(self.processPG)
    self.dlg.bRefreshConnections.clicked.connect(self.getPSQLConnections)
    self.dlg.schemaAdd.clicked.connect(self.addNewSchema)
    """self.dlg.QueryType.activated.connect(self.setQueryType)
      self.dlg.checkAutoCompiled.stateChanged.connect(self.queryGen)
      self.dlg.LAYERa.activated.connect(self.setLAYERa)
      self.dlg.SCHEMAb.activated.connect(self.setSCHEMAb)
      self.dlg.FILTERSCHEMA.activated.connect(self.setFILTERSCHEMA)
      self.dlg.LAYERb.activated.connect(self.setLAYERb)
      self.dlg.FIELD.activated.connect(self.setFIELD)
      self.dlg.SPATIALREL.activated.connect(self.setSPATIALREL)
      self.dlg.SPATIALRELNOT.stateChanged.connect(self.setSPATIALRELNOT)
      self.dlg.checkCreateView.clicked.connect(self.checkCreateView)
      self.dlg.BUFFERRADIUS.textChanged.connect(self.setBUFFERRADIUS)
      self.dlg.ButtonRun.clicked.connect(self.runQuery) #"""


  def show(self):
    if self.PQBdockwidget: # show the widget
      if not self.PQBdockwidget.isVisible():  self.PQBdockwidget.show()
      return  #self.PQBdockwidget.hide()
    
    self.dlg = corrVectorDialog()
    self.PQBdockwidget=QDockWidget( self.nomDuMenu, iface.mainWindow() )
    self.PQBdockwidget.setObjectName("Corrector")
    self.PQBdockwidget.setWidget(self.dlg)
    self.PQBdockwidget.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
    iface.addDockWidget( Qt.RightDockWidgetArea, self.PQBdockwidget )
    self.PQBdockwidget.show()
    #defaults
    #self.dlg.GEOMETRYFIELD.setText("the_geom")
    #self.dlg.KEYFIELD.setText("ogc_fid")
    self.predefinedLayer = None
    
    self.dlg.layerComboBoxSource.setFilters( QgsMapLayerProxyModel.PolygonLayer ) # VectorLayer 
    #hide Temp slots  
    self.dlg.layerComboBoxArrows.setFilters( QgsMapLayerProxyModel.LineLayer  ) 
    #self.dlg.layerComboBoxArrows.hide()
    """self.dlg.USERFIELD.hide()
    self.dlg.USERFIELDLabel.hide()
    self.dlg.PASSWORDFIELD.hide()
    self.dlg.PASSWORDFIELDLabel.hide() #"""
    #self.dlg.reloadButton.setIcon(QIcon(os.path.join(self.plugin_dir,"svg","reload.svg")))
    #init
    self.PSQL = PSQL(iface)
    self.getPSQLConnections()
    #self.populateGui()
    self.eventsConnect()
    #self.toTableDlg= convertToTableDialog(self)
    self.datasource= None


  def createTempArrows(self):
    win= iface.mainWindow()
    source= self.dlg.layerComboBoxSource.currentLayer()
    if not source:
      QMessageBox.warning(win, self.tr("Important!"), self.tr("Please choose first the source layer to deform.") )
      return
    EPSG= source.crs().postgisSrid()
    print("source CRS postgisSrid: ", source.crs().postgisSrid() )
    if EPSG<1 or EPSG>399999:
      authid= source.crs().authid()
      print("source CRS authid: ", authid )
      if 'EPSG:' in authid:
        EPSG= authid.replace('EPSG:','')
      else:
        QMessageBox.warning(win, self.tr("Important!"), self.tr("The CRS of the source layer is undefined or it doesn't have an EPSG number. Please, define the CRS of that layer with an ESPG ID.") )
        return
    print('new arrows layer EPSG :'+ str(EPSG) )
    
    arrowName= self.tr('arrows','layer name')
    arrows= QgsVectorLayer("LineString?crs=EPSG:{0}".format(EPSG), arrowName, "memory")
    arrows.setCrs( QgsCoordinateReferenceSystem("EPSG:{0}".format(EPSG) ) )
    QgsProject.instance().addMapLayer(arrows)
    path= os.path.dirname(__file__) +os.sep +'Style_arrows.qml'
    arrows.loadNamedStyle(path,True)
    arrows.startEditing()
    #arrowspr= arrows.dataProvider()
    #surf= QgsField( "surface", QVariant.Double, "numeric", 20, 15) # Pour afficher la surface de superposition
    #arrowspr.addAttributes( [surf] ) # layer.fields().toList() )
    QMessageBox.warning(win, self.tr("Layer created : ") +arrowName, self.tr("Draw your deformation arrows in the temp layer [{0}] and save the layer before starting the treatment.").format(arrowName) )


  def verifLayers(self, v): ### Before the treatments
    win= iface.mainWindow()
    
    source= self.dlg.layerComboBoxSource.currentLayer()
    if not source:
      QMessageBox.warning(win, self.tr("Important!"), self.tr("Please choose the source layer to deform.") )
      return False
    EPSG= source.crs().postgisSrid()
    print("source CRS postgisSrid: ", EPSG)
    if EPSG<1 or EPSG>399999:
      authid= source.crs().authid()
      print("source CRS authid: ", authid )
      if 'EPSG:' in authid:
        EPSG= authid.replace('EPSG:','')
      else:
        QMessageBox.warning(win, self.tr("Important!"), self.tr("The CRS of the source layer is undefined or it doesn't have an EPSG number. Please, define the CRS of that layer with an ESPG ID.") )
        return False
    #EPSG= str(EPSG)
    
    arrows= self.dlg.layerComboBoxArrows.currentLayer()
    if not arrows:
      QMessageBox.warning(win, self.tr("Important!"), self.tr("Please choose (or create) the layer with deformation vectors (arrows).") )
      return False
    nb= arrows.featureCount()
    print("arrows.featureCount(): ", nb )
    if nb<1:
      arrows.commitChanges()
      nb= arrows.featureCount()
      if nb<1 and len(list(arrows.getFeatures()))<1:
        QMessageBox.warning(win, self.tr("Important!"), self.tr("The layer with deformation vectors (arrows) is empty. Please draw the arrows first.") )
        return False
    print("arrows CRS postgisSrid: ", arrows.crs().postgisSrid() )
    v.append(source) ; v.append(arrows) ; v.append(EPSG)
    return True


  def createTempDB(self):
    s= QSettings()
    dbpath= s.value(self.params+"tempDB", "")
    if dbpath!='' and os.path.exists(dbpath):
      print( 'Old DB: '+ dbpath )
      con= spatialite_connect( dbpath )
      cur= con.cursor()
      #cur.execute("BEGIN")
      cur.execute( "SELECT DropGeoTable('poly')" )
      cur.execute( "SELECT DropGeoTable('arrows')" )
      cur.execute( "DELETE FROM geometry_columns_time WHERE f_table_name='poly'" )
      cur.execute( "DELETE FROM geometry_columns_time WHERE f_table_name='arrows'" )
      cur.execute( "DELETE FROM spatialite_history WHERE table_name='poly'" )
      cur.execute( "DELETE FROM spatialite_history WHERE table_name='arrows'" )
      #sql = u"DELETE FROM geometry_columns WHERE upper(f_table_name) = upper(%s)" % dbpath
      con.commit()
      con.close()
      #self.dropTable('poly', 'geom')
      #self.dropTable('arrows', 'geom')
      return dbpath
    fp= tempfile.TemporaryFile(suffix='.sqlite')
    dbpath= fp.name
    print( 'New DB: '+ dbpath )
    fp.close()
    con= spatialite_connect( dbpath, isolation_level=None)
    cur= con.cursor()
    cur.execute("BEGIN")
    sql= "SELECT InitSpatialMetadata()"
    cur.execute(sql)
    #sql = "CREATE TABLE test_pg (id INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL)"
    #cur.execute(sql)
    #sql = "SELECT AddGeometryColumn('test_pg', 'geometry', 4326, 'POLYGON', 'XY')"
    #cur.execute(sql)
    con.commit()
    con.close()
    s.setValue(self.params+"tempDB", dbpath)
    return dbpath



  def processSpatialite(self): ### The treatment with Spatialite (SP) : without PostGIS
    win= iface.mainWindow()
    var=[]
    if not self.verifLayers(var): return
    source= var[0] ; arrows= var[1] ; EPSG= var[2]
    
    dbpath= self.createTempDB()
    uri = QgsDataSourceUri()
    uri.setDatabase( dbpath )
    
    #print( self.layerDelete( SCHEMA, newtable, cascade=True ) )
    selec= self.dlg.checkSelec.isChecked()
    if not self.exportToSP( uri, source, 'poly', EPSG, 'grefuid', selec ):
      QMessageBox.warning(win, self.tr("Problem!"), self.tr("Couldn't create temporary layer with [%s]. Process failed.")% source.name() )
      print("Echec chargement de %s dans Spatialite"% source.name() )
      return
    if not self.exportToSP( uri, source, 'newpoly', EPSG, 'nrefuid', selec ):
      QMessageBox.warning(win, self.tr("Problem!"), self.tr("Couldn't create temporary layer with [%s]. Process failed.")% source.name() )
      print("Echec chargement de %s dans Spatialite"% source.name() )
      return
    #self.layerDelete( SCHEMA, arrowTable, cascade=True )
    if not self.exportToSP( uri, arrows, "arrows", EPSG ):
      QMessageBox.critical(win, self.tr("Problem!"), self.tr("Couldn't create temporary layer with [%s]. Process failed.")% arrows.name() )
      print("Echec chargement de %s dans Spatialite"% arrows.name() )
      return
    
    
    db = QSqlDatabase.addDatabase("QSPATIALITE") # Create DB connexion
    db.setDatabaseName(uri.database()) # the path to DB
    db.open()
    query= QSqlQuery()
    
    self.msgSP(self.tr("Prepare layer with deformations from your arrows: step 1"))
    ### SQL queries :              
    
    uri.setTable('poly')
    uri.setGeometryColumn('geom')
    polyTemp= QgsVectorLayer(uri.uri(), "poly", 'spatialite')
    layWidth= polyTemp.extent().width()
    # t1 = points d'un buffer autour de poly :
    query.exec_("DROP TABLE IF EXISTS t1")
    r= query.exec_("""CREATE TABLE t1  AS
      WITH uu AS ( SELECT ST_Collect(ST_StartPoint(geom)) geom FROM arrows
        UNION  SELECT ST_Collect(geom) geom FROM poly )
      SELECT ST_DissolvePoints( ExteriorRing( ST_Buffer( ST_Buffer(ST_Collect(geom),{0},3), -{1}, 1) )) geometry
        FROM uu """.format(layWidth, layWidth*9/10) )
    #SELECT ST_DissolvePoints( ExteriorRing( ST_Buffer( ST_Collect(geom),1000,1 ) ) ) geometry  FROM poly
    if not r:  return self.errorSP(query)
    query.exec_("SELECT RecoverGeometryColumn('t1', 'geometry', {0}, 'MULTIPOINT', 'XY')".format(EPSG) )
    
    # Creer couche de points de recalage, base pour la triangulation,
    #   ils vont entourer poly et accueillir les vecteurs (conv en points) :
    query.exec_("SELECT DiscardGeometryColumn('trecal', 'geom')")
    query.exec_("DROP TABLE IF EXISTS trecal")
    query.exec_("CREATE TABLE trecal ( uid INTEGER PRIMARY KEY AUTOINCREMENT, deltax real, deltay real )" )
    query.exec_("SELECT AddGeometryColumn('trecal', 'geom', {0}, 'POINT', 'XY')".format(EPSG) )
    query.exec_("""WITH aa AS ( SELECT mp.rowid id, e.item_no part, e.geometry  FROM t1 AS mp
        JOIN ElementaryGeometries AS e ON (e.f_table_name = 't1' AND e.origin_rowid = mp.rowid) )
      INSERT INTO trecal (geom)  SELECT geometry geom  FROM aa""")
    # Retirer le 1er pt du buffer qui est en doublon avec le dernier :
    query.exec_("DELETE FROM trecal WHERE uid=1")
    
    # Ajouter les vecteurs de recalage convertis en points avec les infos de décalage x et y :
    query.exec_("""INSERT INTO trecal (deltax, deltay, geom)  SELECT
      ST_X(ST_EndPoint(v.geom))-ST_X(ST_StartPoint(v.geom)) deltax,
      ST_Y(ST_EndPoint(v.geom))-ST_Y(ST_StartPoint(v.geom)) deltay,
      ST_StartPoint(v.geom) geom
     FROM arrows v """)
    
    # Chercher a attribuer deltax et y proportionnels aux pts trecal qui n en ont pas encore :
    query.exec_("""WITH nu AS ( SELECT uid idnu, geom g1  FROM trecal  WHERE deltax IS NULL ) 
, aa AS (   SELECT idnu, uid idval, deltax x, deltay y, geom, ST_Distance(g1,geom) dist
  FROM nu, trecal  WHERE deltax IS NOT NULL  )
, min1 AS (  SELECT  idnu idmin, min( dist ) mini FROM aa  GROUP BY  idnu  )
, v1 AS (  SELECT idnu, idval, x x1, y y1, geom g1, dist d1  FROM aa
  INNER JOIN min1  ON idnu = idmin  AND dist=mini  )
, min2 AS (  SELECT aa.idnu idmin, min( dist ) mini FROM aa, v1
  WHERE aa.idnu=v1.idnu AND aa.idval<>v1.idval  GROUP BY  aa.idnu  )
, v2 AS (  SELECT idnu, idval, x x2, y y2, geom g2, dist d2  FROM aa
  INNER JOIN min2 ON idnu=idmin  AND dist=mini )
, cc AS (  SELECT  v1.idnu, x1, x2, y1, y2, g1, g2, d1, d2, ST_Distance(g1,g2) d3
  FROM v1, v2  WHERE v1.idnu=v2.idnu  )
, compar AS ( SELECT idnu,
 CASE 
  WHEN x1=x2 THEN x1
	WHEN d1=d2 THEN (x1+x2)/2  -- équidistance donc on applique la moyenne
	-- on a forcément dd[1]<dd[2] à cause du ORDER BY dist : idnu est plus proche de g1
	  -- angle droit entre A et B :  diag²=A²+B²  ; dd[2] est la diagonale :
		--  chercher si l'angle suivant dépasse 90°: entre dd[1] et la ligne gg[1]-gg[2]
		-- si diag²>=d1²+d2² alors appliquer la valeur xx[1]
	WHEN power(d2,2) >= power(d1,2) + power(d3,2) THEN x1
	  -- x2=x1+diff ;   (x1+x1+diff)/2 = x1 + diff*0.5
	   -- à angle droit on a diff=0  et  d2²=d1²+dist(g1-g2)²  donc  d1²+dist(g1-g2)²-d2² = 0
		 -- à équidistance on a diff=0.5  et  d1²=d2²  donc 0.5 * d1²+dist(g1-g2)²-d2² / dist(g1-g2)² = 0.5
	  -- d1²=d2²+F ; F=d1²-d2² ; 90°: F=dist(g1-g2)²  ;  équidistance: F=0
		-- V= x1+diff*N  ;  90°: N=0  ;  équidistance: N=0.5
		-- d1²-d2² / dist(g1-g2)² * 0.5 = diff  ;  x1 = x2-diff  ; V= x1 + (x2-x1)*diff
	ELSE x1 + (x2-x1) * 0.5 * (power(d1,2)+power(d3,2)-power(d2,2)) / power(d3,2)
 END newx ,
 CASE 
  WHEN y1=y2 THEN y1
	WHEN d1=d2 THEN (y1+y2)/2  -- équidistance donc a applique la moyenne
	-- on a forcément dd[1]<dd[2] à cause du ORDER BY dist : idnu est plus proche de g1
	WHEN power(d2,2) >= power(d1,2) + power(d3,2) THEN y1
	ELSE y1 + (y2-y1) * 0.5 * (power(d1,2)+power(d3,2)-power(d2,2)) / power(d3,2)
 END newy
 FROM cc 
)
UPDATE trecal SET deltax=(SELECT newx FROM compar WHERE uid=idnu), deltay=(SELECT newy FROM compar WHERE uid=idnu)
  WHERE uid IN (SELECT idnu FROM compar) """)
    
    
    self.msgSP(self.tr("Exploding your polygons to points"))
    # Exploser les polygones en points avec numerotation : id objet, part, numring et numpt
    #  d'abord en anneaux (MULTIPOINTs) :
    query.exec_("SELECT DiscardGeometryColumn('zanneaux', 'geom')")
    query.exec_("SELECT DiscardGeometryColumn('zanneaux', 'polygo')")
    query.exec_("DROP TABLE IF EXISTS zanneaux")
    query.exec_("CREATE TABLE zanneaux ( pkuid INTEGER PRIMARY KEY AUTOINCREMENT, id INTEGER, part INTEGER, numring INTEGER, nbi INTEGER)")
    query.exec_("SELECT AddGeometryColumn('zanneaux', 'geom', {0}, 'MULTIPOINT', 'XY')".format(EPSG) )
    query.exec_("SELECT AddGeometryColumn('zanneaux', 'polygo', {0}, 'POLYGON', 'XY')".format(EPSG) )
    # First get the exterior ring(s) of each object (exploding them into single parts) :
    #query.exec_(""" WITH aa as ( SELECT mp.rowid id, e.item_no part, e.geometry  FROM poly AS mp
    query.exec_(""" WITH aa as ( SELECT grefuid id, e.item_no part, e.geometry  FROM poly AS mp
       JOIN ElementaryGeometries AS e ON (e.f_table_name = 'poly' AND e.origin_rowid = mp.rowid) )
      INSERT INTO zanneaux (id, part, numring, nbi, geom, polygo)
       SELECT id, part, 0 numring, ST_NumInteriorRing(geometry) nbi, 
        ST_DissolvePoints(ExteriorRing(geometry)) geom, geometry polygo  FROM aa """)
    # Then get the interior rings of each object :
    query.exec_(""" WITH RECURSIVE aa(pkuid, nbi) as ( SELECT pkuid, nbi FROM zanneaux  WHERE nbi>0 )
      , cnt(uid, n, x) AS ( SELECT pkuid, nbi, 1 FROM aa
        UNION ALL  SELECT uid, n, x+1 FROM cnt WHERE x<n )
      INSERT INTO zanneaux (id, part, numring, geom)
       SELECT id, part, x numring, ST_DissolvePoints( InteriorRingN(polygo,x) ) geom FROM zanneaux, cnt
        WHERE uid=pkuid """)
    
    # Enfin en points :
    query.exec_("SELECT DiscardGeometryColumn('tpoints', 'geom')")
    query.exec_("DROP TABLE IF EXISTS tpoints")
    query.exec_("CREATE TABLE tpoints ( pkuid INTEGER PRIMARY KEY AUTOINCREMENT, deltax real, deltay real, idg INTEGER, part INTEGER, numring INTEGER, numpt INTEGER)")
    query.exec_("SELECT AddGeometryColumn('tpoints', 'geom', {0}, 'POINT', 'XY')".format(EPSG) )
    
    query.exec_(""" INSERT INTO tpoints (idg, part, numring, numpt, geom)
     SELECT id idg, part, numring, e.item_no numpt, e.geometry AS geom  FROM zanneaux AS mp
      JOIN ElementaryGeometries AS e  ON
       (e.f_table_name='zanneaux' AND e.f_geometry_column='geom' AND e.origin_rowid = mp.rowid) """)
    
    
    self.msgSP(self.tr("Preparing 2 triangulation layers from step 1"))
    ###  processing
    
    uri.setTable('trecal')
    uri.setGeometryColumn('geom')
    trecal= QgsVectorLayer(uri.uri(), "trecal", 'spatialite')
    QgsProject.instance().addMapLayer(trecal)
    dbFile= trecal.dataProvider().dataSourceUri() # uri.database().replace('\\','\\\\')
    #print( dbFile ) 
    # delta X :
    """param= { 'INTERPOLATION_DATA': dbFile +"::~::0::~::1::~::0", 'METHOD': 0, 'PIXEL_SIZE': layWidth/500, 'EXTENT': trecal, 'OUTPUT': 'TEMPORARY_OUTPUT' }
    try: resX= processing.run("qgis:tininterpolation", param ) #"""
    param= { 'INTERPOLATION_DATA': dbFile +"::~::0::~::1::~::0", 'DISTANCE_COEFFICIENT': 2, 'PIXEL_SIZE': layWidth/500, 'EXTENT': trecal, 'OUTPUT': 'TEMPORARY_OUTPUT' }
    try: resX= processing.run("qgis:idwinterpolation", param )    
    except:
      QMessageBox.critical(win, self.tr("Problem!"), self.tr("The process failed at triangulation (TINinterpolation).") )
      return
    print( resX['OUTPUT'] )
    #QgsProject.instance().addMapLayer(resX['OUTPUT'])
    
    uri.setTable('tpoints')
    uri.setGeometryColumn('geom')
    tpoints= QgsVectorLayer(uri.uri(), "tpoints", 'spatialite')
    param= { 'COLUMN_PREFIX' : 'xvalue', 'INPUT': tpoints, 'OUTPUT': 'TEMPORARY_OUTPUT', 'RASTERCOPY': resX['OUTPUT'] }
    res= processing.run("qgis:rastersampling", param )
    layerX= res['OUTPUT']
    
    self.msgSP("Intersects each points with the 2 tin layers to interpolate their deplacement")
    # delta Y :
    """param= { 'INTERPOLATION_DATA': dbFile +"::~::0::~::2::~::0", 'METHOD': 0, 'PIXEL_SIZE': layWidth/500, 'EXTENT': trecal, 'OUTPUT': 'TEMPORARY_OUTPUT' }
    resY= processing.run("qgis:tininterpolation", param ) #"""
    param= { 'INTERPOLATION_DATA': dbFile +"::~::0::~::2::~::0", 'DISTANCE_COEFFICIENT':2, 'PIXEL_SIZE':layWidth/500, 'EXTENT':trecal, 'OUTPUT':'TEMPORARY_OUTPUT' }
    resY= processing.run("qgis:idwinterpolation", param )    
    
    param= { 'COLUMN_PREFIX':'yvalue', 'INPUT':layerX, 'OUTPUT':'TEMPORARY_OUTPUT', 'RASTERCOPY':resY['OUTPUT'] }
    res= processing.run("qgis:rastersampling", param )
    layerXY= res['OUTPUT']
    #QgsProject.instance().addMapLayer(layerXY)
    
    QgsProject.instance().removeMapLayer(trecal)
    
    self.msgSP(self.tr("Moving each point"))
    ### Import du resultat dans spatialite : 
    if not self.exportToSP( uri, layerXY, 'tpointsdepla', EPSG, 'pkuid' ):
      QMessageBox.warning(win, self.tr("Problem!"), self.tr("Failed to import 'tpointsdepla' into Spatialite.") )
      print("Echec chargement de  dans Spatialite")
      return
    
    ### Deplacer les point par deltax et y :
    time.sleep(1)
    r= query.exec_("UPDATE tpointsdepla SET geom=ST_Translate(geom,xvalue_1,yvalue_1,0)" )
    if not r:
      time.sleep(1)
      r= query.exec_("UPDATE tpointsdepla SET geom=ST_Translate(geom,xvalue_1,yvalue_1,0)" )
      if not r: return self.errorSP(query)
    
    self.dropTable('trings', 'geom')
    r= query.exec_("""CREATE TABLE trings AS
      WITH gr1 AS ( SELECT idg, part p1, numring p2, MakeLine(geom) as geom
        FROM tpointsdepla  GROUP BY idg, part, numring  ORDER BY numpt )
      SELECT idg, p1, p2, ST_IsRing(geom) ringvalid, geom  FROM gr1""" )
    if not r:  return self.errorSP(query)
    query.exec_("SELECT RecoverGeometryColumn('trings', 'geom', {0}, 'LINESTRING', 'XY')".format(EPSG) )
    
    
    self.msgSP( self.tr("Rebuild the polygons with the points that were moved") )
    ### Reassembler les anneaux en polygones (anneaux externes et internes) :
    r= query.exec_(""" WITH grext AS ( SELECT idg, p1, geom exter FROM trings  WHERE p2=0 AND ringvalid )
      ,grint AS ( SELECT idg, p1, Collect(geom) inter FROM trings
        WHERE p2>0 AND ringvalid  GROUP BY idg, p1  )
      ,monos AS ( SELECT grext.idg,
          CASE WHEN inter IS NULL THEN ST_MakePolygon(exter)
          ELSE ST_MakePolygon( exter, inter )
          END geom  FROM grext
        LEFT JOIN grint  ON grext.idg = grint.idg  AND  grext.p1 = grint.p1 )
      ,multis AS ( SELECT idg, ST_Multi( ST_Collect(geom) ) g3 FROM monos  GROUP BY idg )
     UPDATE newpoly SET geom=( SELECT g3 FROM multis m  WHERE nrefuid = m.idg )
        WHERE nrefuid IN (SELECT idg FROM multis)""" )
    if not r:  return self.errorSP(query)
    
    
    self.msgSP( '--- '+ self.tr("The end") +' ---' )
    uri.setTable('newpoly')
    uri.setGeometryColumn('geom')
    newpoly= QgsVectorLayer(uri.uri(), "corrected", 'spatialite')
    QgsProject.instance().addMapLayer(newpoly)
    
    QMessageBox.information(win, self.tr("End"), self.tr("""You may inspect the objects in the layer "corrected".\nIf they are not okay, you can move your arrows or add new ones, and restart the process.""") )
    
    db.close()


  def msgSP(self, msg=''): ### Show msg during SP process (not in QThread)
    self.dlg.lineMessage.setText(msg)
    QApplication.instance().processEvents() # Pour afficher messages immediatement


  def exportToSP(self, uri, layer, newtable, srid, IDPK='pkuid', selec= False):
    options= QgsVectorFileWriter.SaveVectorOptions()
    options.actionOnExistingFile= QgsVectorFileWriter.CreateOrOverwriteLayer 
    options.layerName= newtable
    options.driverName= "SQLite"
    transform= QgsCoordinateTransform(layer.crs(), QgsCoordinateReferenceSystem("EPSG:{0}".format(srid) ), QgsProject.instance())
    options.ct= transform
    options.datasourceOptions= ['SPATIALITE=YES']
    options.layerOptions= ['GEOMETRY_NAME=geom', 'FID='+IDPK, "SRID="+str(srid)]
    options.onlySelectedFeatures= selec
    #QgsVectorFileWriter.writeAsVectorFormatV2(layer, uri.database(), QgsCoordinateTransformContext(), options)
    err, msg = QgsVectorFileWriter.writeAsVectorFormat(layer, uri.database(), options)
    if err == QgsVectorFileWriter.NoError:
      print('export to spatialite OK: '+ newtable)
      return True
    else:
      QMessageBox.warning(None, self.tr("Problem!"), self.tr("Import into spatialite failed.\n{0}").format(msg) )
      return False
    
  def OLD_exportToSpa(self, uri, layer, newtable, IDPK='pkuid', selec= False): # Fails when table already exists
    uri.setTable(newtable)
    uri.setKeyColumn(IDPK)
    uri.setGeometryColumn('geom')
    destCRS= layer.crs()
    err, msg= QgsVectorLayerExporter.exportLayer( layer, uri.uri(), 'spatialite', destCRS, selec )
    #,feedback=feedbackZZ
    # err  is QgsVectorLayerExporter.ExportError
    if err == QgsVectorLayerExporter.NoError:
      print('export to spatialite OK')
      return True
    else:
      QMessageBox.warning(None, self.tr("Problem!"), self.tr("Export to spatialite failed.\n{0}").format(msg) )
      return False


  def errorSP(self, query):
    QMessageBox.critical( iface.mainWindow(), self.tr("Problem!"), self.tr("Process failed:\nSQL error:\n") +query.lastError().text() +"\nQuery:\n"+ query.lastQuery() )
    return False


  def dropTable(self, table, geom=''): 
    query= QSqlQuery()
    query.exec_("SELECT DropGeoTable('{0}')".format(table) )
    query.exec_("DELETE FROM geometry_columns_time WHERE f_table_name='{0}'".format(table) )
    return True
    
    if geom!='':
      query.exec_("SELECT DiscardGeometryColumn('{0}','{1}')".format(table,geom) )
    query.exec_('DROP TABLE {0}'.format(table) )
    query.exec_('SELECT 1 FROM {0}'.format(table) )
    query.next()
    if not query.isValid(): return True
    #print( query.isValid(), query.value(0) )
    return False




  def processPG(self): ### The treatment with PostGIS (PG)
    win= iface.mainWindow()
    if not self.datasource:
      QMessageBox.warning(win,self.tr("Important!"),self.tr("Please choose the PostGIS connection.") ) #  print("Il fait d'abord établir une connexion PG")
      return
    uri= self.datasource
    # Table PG où sont dessinées les flèches de recalage : des lignes simples bien orientées :
    SERVEUR= uri.host() #  '192.168.1.11' #'localhost'
    NOMBASE= uri.database() #  'cadastre'
    PGUSER= uri.username() #  'postgres'
    PGMDP= uri.password() #  'postgres'
    
    SCHEMA= self.dlg.DBSchema.currentText()
    if not SCHEMA:
      QMessageBox.warning(win,self.tr("Important!"),self.tr("Please choose the working schema.") ) # print("Il fait d'abord choisir le schéma de travail")
      return
    newtable= "newlayer"
    POLYGONES='"%s"."%s"'% (SCHEMA,newtable)
    POLYGONES_PK='correc_pkuid'
    arrowTable= "vecteurs"
    FLECHES='"%s"."%s"'% (SCHEMA,arrowTable)
    
    var=[]
    if not self.verifLayers(var): return
    source= var[0] ; arrows= var[1] ; EPSG= var[2]
    
    self.msgPG( self.tr("Importing the layers into PostGIS...") )
    print( self.layerDelete( SCHEMA, newtable, cascade=True ) )
    if not self.exportToPG(source, SCHEMA, newtable, EPSG, False, POLYGONES_PK):
      QMessageBox.warning(win, self.tr("Problem!"), self.tr("Failed to import layer %s into Postgis.\nPlease check your rights in that schema.")% source.name() )
      return
    
    self.layerDelete( SCHEMA, arrowTable, cascade=True )
    if not self.exportToPG(arrows, SCHEMA, "vecteurs", EPSG, False, POLYGONES_PK):
      QMessageBox.warning(win, self.tr("Problem!"), self.tr("Failed to import layer %s into Postgis.\nPlease check your rights in that schema.")% arrows.name() )
      return
    
    
    self.msgPG( self.tr("PostGIS processing : please wait...") )
    print('Execution du script de recalage' )
    script= "deform_polygons_pg.sql"
    _dir= os.path.dirname(__file__) + os.sep
    
    #pg= 'psql -h '+SERVEUR+' -U '+PGUSER+' -p 5432 -d '+NOMBASE+' --set=SCHEM='+SCHEMA+' --set=NEWLAYER='+POLYGONES+' --set=IDPK='+POLYGONES_PK+' --set=FLECHES='+FLECHES+' -f "'+_dir+script+'"'
    pg = ['psql','-h',SERVEUR,'-U',PGUSER,'-p','5432','-d',NOMBASE,'--set=SCHEM='+SCHEMA,'--set=EPSG='+str(EPSG),
      '--set=NEWLAYER='+POLYGONES,'--set=IDPK='+POLYGONES_PK,'--set=FLECHES='+FLECHES,'-f',_dir+script ]
    #output = subprocess.check_output( pg, stderr=subprocess.STDOUT, shell=True )
    process= subprocess.Popen(pg, stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
      creationflags=subprocess.CREATE_NO_WINDOW)
    log= ""
    for line in process.stdout:
      #print(line.decode(), end='')
      log+= line.decode()
    
    print("returncode = ", process.returncode ) 
    
    try:  outs, errs = process.communicate(timeout=300) # 5 min
    except subprocess.TimeoutExpired:
      process.kill()
      outs, errs = process.communicate()
      iface.messageBar().pushMessage( self.tr("The SQL script was frozen and had to be terminated. See the Log tab below"), Qgis.Warning, 10)
    
    self.dlg.historyLog.appendPlainText(log)
    
    print("errs=",errs,"  outs=",outs) 
    if process.returncode!=0 :
      self.msgPG( self.tr("SQL error. See the Log tab below") )
      iface.messageBar().pushMessage( self.tr("SQL error. See the Log tab below"), Qgis.Warning, 10)
      return
    
    self.msgPG( '--- '+ self.tr("The end") +' ---' )
    
    connec= "host="+SERVEUR+" port=5432 user='"+PGUSER+"' password='"+PGMDP+"' dbname='"+NOMBASE+"' table=\"recaler\".\"tpolygones\" (geom)"
    uri.setSchema(SCHEMA)
    uri.setTable(newtable)
    #uri.setKeyColumn(pk)
    uri.setGeometryColumn('geom')
    macouche= QgsVectorLayer( uri.uri(), 'corrected', 'postgres')
    QgsProject.instance().addMapLayer(macouche)
    QMessageBox.information(win, self.tr("End"), self.tr("""You may inspect the objects in the layer "corrected".\nIf they are not okay, you can move your arrows or add new ones, and restart the process.""") )


  def msgPG(self, msg=''): ### Show msg during PG process (not in QThread)
    self.dlg.lineMessagePG.setText(msg)
    QApplication.instance().processEvents() # Pour afficher messages immediatement


  def exportToPG(self, qgislayer, schema, table, srid, onlySelected=False, pk='correc_pkuid'):
    if not self.datasource:  return
    if not qgislayer:  return
    """   # resolve connection details to uri
    try: # For QGIS >= 3.10 :
      md= QgsProviderRegistry.instance().providerMetadata('postgres')
      conn = md.createConnection('portable cadastre')
    except: # For QGIS 3.0 to 3.8.x :     # QgsProviderConnectionException:
      uri = QgsDataSourceUri()
      self.db.setHostName(uri.host())
      self.db.setPort(int(uri.port()))
      self.db.setDatabaseName(uri.database())
      self.db.setUserName(uri.username())
      self.db.setPassword(uri.password())
    #"""
    print("Export layer %s to Postgre %s.%s"%(qgislayer.name(),schema,table) )
    uri= self.datasource
    uri.setSchema(schema)
    uri.setTable(table)
    uri.setKeyColumn(pk)
    uri.setGeometryColumn('geom')
    
    #destCRS= qgislayer.crs() # QgsCoordinateReferenceSystem
    destCRS= QgsCoordinateReferenceSystem(srid)
    #feedbackZZ= QgsFeedback()
    err, msg= QgsVectorLayerExporter.exportLayer( qgislayer, uri.uri(), 'postgres', destCRS, onlySelected ) # , feedback=feedbackZZ
    # err  is QgsVectorLayerExporter.ExportError
    if err == QgsVectorLayerExporter.NoError:  return True
    else:
      QMessageBox.information(None, "DB ERROR:", self.tr('Error importing into PostGIS\n{0}').format(msg) )
      return False
    """ feedback ?
      features = qgislayer.getFeatures()
      total = 100.0 / qgislayer.featureCount() if qgislayer.featureCount() else 0
      for current, f in enumerate(features):
          if feedback.isCanceled():  break

          if not exporter.addFeature(f, QgsFeatureSink.FastInsert):
              feedback.reportError(exporter.errorMessage())

          feedback.setProgress(int(current * total))

      exporter.flushBuffer()
      if exporter.errorCode() != QgsVectorLayerExporter.NoError:
          raise QgsProcessingException(
              self.tr('Error importing to PostGIS\n{0}').format(exporter.errorMessage()))

      if geomColumn and createIndex:
          try:
              options = QgsAbstractDatabaseProviderConnection.SpatialIndexOptions()
              options.geometryColumnName = geomColumn
              conn.createSpatialIndex(schema, table, options)
          except QgsProviderConnectionException as e:
              raise QgsProcessingException(self.tr('Error creating spatial index:\n{0}').format(e))

      try:
          conn.vacuum(schema, table)
      except QgsProviderConnectionException as e:
          feedback.reportError(self.tr('Error vacuuming table:\n{0}').format(e)) #"""


  def getPSQLConnections(self):
    try:  self.dlg.PSQLConnection.activated.disconnect(self.setConnection)
    except:  pass
    conn= self.PSQL.getConnections()
    self.populateComboBox(self.dlg.PSQLConnection,conn,"Select connection",True)
    ###self.hideQueryDefSlot()
    self.dlg.PSQLConnection.activated.connect(self.setConnection)

  def setConnection(self):
    if self.dlg.PSQLConnection.currentText()[:6] == "Select":  return
    self.datasource= self.PSQL.setConnection(self.dlg.PSQLConnection.currentText())
    if not self.datasource:  return
    #print "SCHEMAS",self.PSQL.getSchemas()
    schemas = self.PSQL.getSchemas()
    self.populateComboBox(self.dlg.DBSchema,schemas,"Select schema",True)
    return
    self.dlg.DBSchema.activated.connect(self.loadPSQLLayers)
    for r in range(0,self.dlg.DBSchema.count()):
      if self.dlg.DBSchema.itemText(r) == "public":
        self.dlg.DBSchema.setCurrentIndex(r)
        self.dlg.DBSchema.removeItem(0)
        self.loadPSQLLayers()
    
  def populateComboBox(self,combo,list,predef,sort):
    #procedure to fill specified combobox with provided list
    combo.blockSignals (True)
    combo.clear()
    model=QStandardItemModel(combo)
    predefInList = None
    for elem in list:
        try:
            item = QStandardItem(str(elem))
        except TypeError:
            item = QStandardItem(str(elem))
        model.appendRow(item)
        if elem == predef:
            predefInList = elem
    if sort:
        model.sort(0)
    combo.setModel(model)
    if predef != "":
        if predefInList:
            combo.setCurrentIndex(combo.findText(predefInList))
        else:
            combo.insertItem(0,predef)
            combo.setCurrentIndex(0)
    combo.blockSignals (False)


  def addNewSchema(self):
    if not self.datasource:
      QMessageBox.warning(self.dlg, 'Attention', "Il faut d'abord choisir la base de données PostGIS (connexion QGIS)")
      return False
    newSchema, ok= QInputDialog.getText(self.dlg, "Nouveau schéma", "Saisir son nom :", QLineEdit.Normal )
    if not ok or newSchema=='': return
    #newSchema = renameDialog.rename("new_schema")
    error= self.PSQL.addSchema(newSchema)
    if error:
      QMessageBox.information(None, "Attention : erreur PostgreSQL", error)
      return
    schemas= self.PSQL.getSchemas()
    for v in ['topology','tiger','tiger_data']:
      if v in schemas: schemas.remove(v)
    self.populateComboBox( self.dlg.DBSchema, schemas, self.dlg.DBSchema.toolTip(), True )
    self.dlg.DBSchema.setCurrentText(newSchema)


  def layerDelete(self, schema, layer, cascade=None):
    if cascade:  cascadeDirective= " CASCADE"
    else:  cascadeDirective= ""
    sql = 'DROP TABLE IF EXISTS "%s"."%s"%s' % (schema,layer,cascadeDirective)
    """if self.PSQL.isTable(layer): sql = 'DROP TABLE "%s"."%s"%s' % (schema,layer,cascadeDirective)
    elif self.PSQL.isView (layer): sql = 'DROP VIEW "%s"."%s"%s' % (schema,layer,cascadeDirective)
    elif self.PSQL.isMaterializedView (layer): sql = 'DROP MATERIALIZED VIEW "%s"."%s"%s' % (schema,layer,cascadeDirective)
    else: sql ="" #"""
    print( sql )
    return self.PSQL.submitCommand(sql, log = None)
    
    
    msg = "Are you sure you want to delete layer '%s' from schema '%s' ?" % (self.selectedLayer,self.PSQL.getSchema())
    reply = QMessageBox.question(None, 'Message', msg, QMessageBox.Yes, QMessageBox.No)
    if reply == QMessageBox.Yes:
      result = self.PSQL.deleteLayer(self.selectedLayer)
      if result:
        if "DROP ... CASCADE" in result:
          msg = result+"\n\nLayer '%s' has dependencies. Do you want to remove all recursively ?" % self.selectedLayer
          reply = QMessageBox.question(None, 'Message', msg, QMessageBox.Yes, QMessageBox.No)
          if reply == QMessageBox.Yes:
              result = self.PSQL.deleteLayer(self.selectedLayer,cascade = True)
              if result:
                  QMessageBox.information(None, "ERROR:", result)
              else:
                  # fix_print_with_import
                  print("CASCADE DELETED", self.selectedLayer)
        else:
            QMessageBox.information(None, "ERROR:", result)
      else:
          # fix_print_with_import
          print("DELETED", self.selectedLayer)
          pass
    self.populateLayerMenu()





class corrVectorDialog(QDialog):
  def __init__(self):
    """QDialog.__init__(self)
      # Set up the user interface from Designer.
      # After setupUI you can access any designer object by doing
      # self.<objectname>, and you can use autoconnect slots - see
      # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
      # #widgets-and-dialogs-with-auto-connect
      self.setupUi(self) """
    super(corrVectorDialog, self).__init__() # Call the inherited classes __init__ method
    uic.loadUi(os.path.join(os.path.dirname(__file__), 'ui_corrector_vector.ui'), self)


