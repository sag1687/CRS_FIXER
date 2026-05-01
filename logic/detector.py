from qgis.core import QgsProject


class CRSDetector:
    def __init__(self, iface):
        self.iface = iface

    def check_layer(self, layer):
        """
        Esegue i 3 check del Modulo 1 e restituisce un dict di risultati.
        """
        results = {
            'issues': [],
            'severity': 'warning',
            'suggestion': 'In attesa di analisi...'
        }

        if not layer.isValid():
            return None

        crs = layer.crs()

        # Check 1: CRS Invalido
        if not crs.isValid():
            results['issues'].append("CRS non definito o invalido.")
            results['severity'] = 'error'
            return results

        # Check 2: Extent Coherence (Gradi vs Metri)
        extent = layer.extent()
        if crs.isGeographic():
            if abs(extent.xMinimum()) > 190 or abs(extent.xMaximum()) > 190:
                results['issues'].append(
                    "Coordinate in metri ma CRS in gradi (WGS84).")
                results['severity'] = 'error'
        else:
            if abs(extent.xMaximum()) < 190 and abs(extent.yMaximum()) < 190:
                results['issues'].append(
                    "Coordinate in gradi ma CRS proiettato.")
                results['severity'] = 'error'

        # Check 3: Project Coherence
        project_crs = QgsProject.instance().crs()
        if project_crs.isValid() and crs != project_crs:
            # Spesso non è un errore, ma un warning utile per i principianti
            pass

        return results if results['issues'] else None
