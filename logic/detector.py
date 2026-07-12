from qgis.core import QgsProject

from ..i18n import normalize_language, text


class CRSDetector:
    def __init__(self, iface):
        self.iface = iface
        self.language = "it"

    def set_language(self, language):
        self.language = normalize_language(language)

    def tr(self, key, **kwargs):
        return text(key, self.language, **kwargs)

    def check_layer(self, layer):
        """
        Esegue i controlli principali e restituisce un dict di risultati.
        """
        results = {
            "issues": [],
            "severity": "warning",
            "suggestion": self.tr("detector.waiting"),
        }

        if not layer.isValid():
            return None

        crs = layer.crs()

        # Check 1: CRS non valido.
        if not crs.isValid():
            results["issues"].append(self.tr("detector.invalid_crs"))
            results["severity"] = "error"
            return results

        # Check 2: coerenza extent, gradi e metri.
        extent = layer.extent()
        if crs.isGeographic():
            if abs(extent.xMinimum()) > 190 or abs(extent.xMaximum()) > 190:
                results["issues"].append(self.tr("detector.meter_in_degree"))
                results["severity"] = "error"
        else:
            if abs(extent.xMaximum()) < 190 and abs(extent.yMaximum()) < 190:
                results["issues"].append(self.tr("detector.degree_in_projected"))
                results["severity"] = "error"

        # Check 3: coerenza con il CRS del progetto.
        project_crs = QgsProject.instance().crs()
        if project_crs.isValid() and crs != project_crs:
            # Spesso non è un errore, ma un warning utile per i principianti
            pass

        return results if results["issues"] else None
