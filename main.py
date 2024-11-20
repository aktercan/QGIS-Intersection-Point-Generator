
from PyQt5.QtWidgets import QAction, QFileDialog, QProgressDialog, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsField, QgsWkbTypes
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QIcon
from rtree import index
import os



class IntersectionPointGenerator:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = QAction(QIcon(os.path.join(self.plugin_dir, 'icon.png')), "Intersection Point Generator", self.iface.mainWindow())
        self.action.triggered.connect(self.run)

    def initGui(self):
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Intersection Point Generator", self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("&Intersection Point Generator", self.action)

    def run(self):
        line_layer_path, _ = QFileDialog.getOpenFileName(None, "Select the Line Shapefile (SERVIS_HATTI_polyline)", "", "Shapefiles (*.shp)")
        polygon_layer_path, _ = QFileDialog.getOpenFileName(None, "Select the Polygon Shapefile (SERVIS_KUTU_region)", "", "Shapefiles (*.shp)")

        if not line_layer_path or not polygon_layer_path:
            QMessageBox.warning(None, "Input Error", "No files selected.")
            return

        line_layer = QgsVectorLayer(line_layer_path, 'SERVIS_HATTI_polyline', 'ogr')
        polygon_layer = QgsVectorLayer(polygon_layer_path, 'SERVIS_KUTU_region', 'ogr')

        if not line_layer.isValid() or not polygon_layer.isValid():
            QMessageBox.critical(None, "Layer Error", "One or more layers failed to load.")
            return

        QgsProject.instance().addMapLayer(line_layer)
        QgsProject.instance().addMapLayer(polygon_layer)

        point_layer = QgsVectorLayer('Point?crs=' + line_layer.crs().toWkt(), 'Intersection Points', 'memory')
        point_layer_provider = point_layer.dataProvider()

        point_layer_provider.addAttributes([QgsField("Polygon_ID", QVariant.Int), QgsField("Line_ID", QVariant.Int)])
        point_layer.updateFields()

        unmatched_lines_layer = QgsVectorLayer('LineString?crs=' + line_layer.crs().toWkt(), 'Unmatched Lines', 'memory')
        unmatched_lines_layer_provider = unmatched_lines_layer.dataProvider()
        unmatched_lines_layer_provider.addAttributes(line_layer.fields().toList())
        unmatched_lines_layer.updateFields()

        unmatched_polygons_layer = QgsVectorLayer('Polygon?crs=' + polygon_layer.crs().toWkt(), 'Unmatched Polygons', 'memory')
        unmatched_polygons_layer_provider = unmatched_polygons_layer.dataProvider()
        unmatched_polygons_layer_provider.addAttributes(polygon_layer.fields().toList())
        unmatched_polygons_layer.updateFields()

        line_features = list(line_layer.getFeatures())
        poly_features = list(polygon_layer.getFeatures())

        idx = index.Index()
        poly_geometries = []
        for pos, poly_feature in enumerate(poly_features):
            poly_geom = poly_feature.geometry()
            poly_geometries.append((poly_feature['ID'], poly_geom))
            idx.insert(pos, poly_geom.boundingBox().toRectF().getCoords())

        new_features = []
        matched_lines = set()
        matched_polygons = set()

        total_steps = len(line_features)
        progress = QProgressDialog("Processing...", "Abort", 0, total_steps)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        for i, line_feature in enumerate(line_features):
            line_geom = line_feature.geometry()
            line_id = line_feature['ID']

            if line_geom.isMultipart():
                points = line_geom.asMultiPolyline()[0]
            else:
                points = line_geom.asPolyline()

            if not points:
                continue

            found_intersection = False
            for point in points:
                point_geom = QgsGeometry.fromPointXY(point)
                possible_polygons = list(idx.intersection(point_geom.boundingBox().toRectF().getCoords()))

                for pos in possible_polygons:
                    poly_id, poly_geom = poly_geometries[pos]
                    if poly_geom.contains(point_geom) or poly_geom.intersects(point_geom):
                        found_intersection = True
                        point_feature = QgsFeature()
                        point_feature.setGeometry(point_geom)
                        point_feature.setAttributes([poly_id, line_id])
                        new_features.append(point_feature)
                        matched_lines.add(line_id)
                        matched_polygons.add(poly_id)

            if not found_intersection:
                unmatched_lines_layer_provider.addFeature(line_feature)

            progress.setValue(i + 1)
            if progress.wasCanceled():
                break

        # Add unmatched polygons to the unmatched polygons layer
        for poly_feature in poly_features:
            poly_id = poly_feature['ID']
            if poly_id not in matched_polygons:
                unmatched_polygons_layer_provider.addFeature(poly_feature)

        # Create an RTree index for line endpoints
        end_points_idx = index.Index()
        line_endpoints = []
        for i, line_feature in enumerate(unmatched_lines_layer.getFeatures()):
            line_geom = line_feature.geometry()
            if line_geom.isMultipart():
                points = line_geom.asMultiPolyline()[0]
            else:
                points = line_geom.asPolyline()

            if points:
                end_point = points[-1]
                end_point_geom = QgsGeometry.fromPointXY(end_point).boundingBox().toRectF().getCoords()
                line_endpoints.append((line_feature['ID'], end_point_geom, end_point, line_feature))
                end_points_idx.insert(i, end_point_geom, obj=i)

        # Check if the endpoints of the unmatched lines intersect the bounding box of any polygon
        for poly_id, poly_geom in poly_geometries:
            possible_end_points = list(end_points_idx.intersection(poly_geom.boundingBox().toRectF().getCoords()))
            for idx in possible_end_points:
                line_id, end_point_geom, end_point, line_feature = line_endpoints[idx]
                if poly_geom.boundingBox().intersects(QgsGeometry.fromPointXY(end_point).boundingBox()):
                    point_feature = QgsFeature()
                    point_feature.setGeometry(QgsGeometry.fromPointXY(end_point))
                    point_feature.setAttributes([poly_id, line_id])
                    new_features.append(point_feature)
                    matched_lines.add(line_id)
                    matched_polygons.add(poly_id)

                # Additional check for full geometry intersection
                line_geom = line_feature.geometry()
                if line_geom.intersects(poly_geom):
                    intersection = line_geom.intersection(poly_geom)
                    if intersection.isMultipart():
                        if intersection.wkbType() == QgsWkbTypes.MultiPoint:
                            points = intersection.asMultiPoint()
                        elif intersection.wkbType() == QgsWkbTypes.MultiLineString:
                            points = [pt for line in intersection.asMultiPolyline() for pt in line]
                    elif intersection.wkbType() == QgsWkbTypes.Point:
                        points = [intersection.asPoint()]
                    elif intersection.wkbType() == QgsWkbTypes.LineString:
                        points = intersection.asPolyline()
                    else:
                        points = []

                    for point in points:
                        point_geom = QgsGeometry.fromPointXY(point)
                        if poly_geom.contains(point_geom) or poly_geom.intersects(point_geom):
                            point_feature = QgsFeature()
                            point_feature.setGeometry(point_geom)
                            point_feature.setAttributes([poly_id, line_id])
                            new_features.append(point_feature)
                            matched_lines.add(line_id)
                            matched_polygons.add(poly_id)

        if new_features:
            point_layer_provider.addFeatures(new_features)
            QgsProject.instance().addMapLayer(point_layer)
            QMessageBox.information(None, "Success", f"{len(new_features)} new points created.")
        else:
            QMessageBox.information(None, "Result", "No intersection points created.")

        QgsProject.instance().addMapLayer(unmatched_lines_layer)
        QgsProject.instance().addMapLayer(unmatched_polygons_layer)

        progress.setValue(total_steps)
