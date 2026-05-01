from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsVectorLayer
import processing


class OneClickFixer:
    def __init__(self, iface):
        self.iface = iface

    def assign_crs(self, layer, crs_auth_id, output_path=None):
        """Ridefinisce il CRS. Se output_path è fornito, salva il risultato."""
        if output_path:
            params = {
                'INPUT': layer,
                'CRS': crs_auth_id,
                'OUTPUT': output_path
            }
            try:
                result = processing.run("native:assignprojection", params)
                if 'OUTPUT' in result:
                    out_layer = QgsVectorLayer(
                        result['OUTPUT'], f"{
                            layer.name()}_{
                            crs_auth_id.replace(
                                ':', '_')}", "ogr")
                    if out_layer.isValid():
                        QgsProject.instance().addMapLayer(out_layer)
                        QgsProject.instance().removeMapLayer(layer.id())
                        return out_layer.id()
            except Exception as e:
                print(f"Errore nell'assegnazione CRS: {e}")
            return False
        else:
            new_crs = QgsCoordinateReferenceSystem(crs_auth_id)
            if new_crs.isValid():
                layer.setCrs(new_crs)
                layer.triggerRepaint()
                return layer.id()
            return False

    def reproject_layer(self, layer, target_crs_auth_id, output_path=None):
        """Crea una copia riproiettata usando l'algoritmo nativo di QGIS."""
        params = {
            'INPUT': layer,
            'TARGET_CRS': target_crs_auth_id,
            'OUTPUT': output_path or 'TEMPORARY_OUTPUT'
        }
        try:
            result = processing.run("native:reprojectlayer", params)
            if 'OUTPUT' in result:
                if output_path:
                    output_layer = QgsVectorLayer(
                        result['OUTPUT'], f"{
                            layer.name()}_{
                            target_crs_auth_id.replace(
                                ':', '_')}", "ogr")
                else:
                    output_layer = result['OUTPUT']
                    output_layer.setName(
                        f"{layer.name()}_{target_crs_auth_id.replace(':', '_')}")

                if output_layer and output_layer.isValid():
                    QgsProject.instance().addMapLayer(output_layer)
                    QgsProject.instance().removeMapLayer(layer.id())
                    return output_layer.id()
        except Exception as e:
            print(f"Errore nella riproiezione: {e}")
        return False

    def fix_all(self, layers_data, suggest_engine):
        """Esegue il batch fix in memoria su tutti i layer segnalati."""
        success_count = 0
        for layer_id, data in layers_data.items():
            layer = QgsProject.instance().mapLayer(layer_id)
            if layer:
                suggestion = suggest_engine.suggest_crs(layer)
                if self.assign_crs(layer, suggestion['id']):
                    success_count += 1
        return success_count
