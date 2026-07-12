import json
import math
import urllib.parse
import urllib.request

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsMessageLog,
    QgsPointXY,
    QgsProject,
)

from ..i18n import normalize_language, text

LOG_TAG = "Quick CRS Fixer"
NETWORK_TIMEOUT_SECONDS = 10
USER_AGENT = "QGIS-QuickCRSFixer-Plugin/2.0"


class SmartSuggest:
    def __init__(self, iface):
        self.iface = iface
        self.language = "it"
        # Database semplificato di EPSG comuni e i loro bounding box (WGS84)
        # Formato: 'EPSG': (xmin, ymin, xmax, ymax, "Nome", "Perché")
        self.crs_db = {
            "EPSG:3003": (
                6.62,
                36.4,
                13.14,
                47.05,
                "Monte Mario / Italy zone 1",
                "Standard per la cartografia tecnica in Italia Ovest.",
            ),
            "EPSG:3004": (
                12.45,
                36.4,
                18.48,
                47.05,
                "Monte Mario / Italy zone 2",
                "Standard per la cartografia tecnica in Italia Est.",
            ),
            "EPSG:32632": (
                6.0,
                0.0,
                12.0,
                84.0,
                "WGS 84 / UTM zone 32N",
                "Sistema globale preciso, molto usato in Europa centrale e Italia.",
            ),
            "EPSG:32633": (
                12.0,
                0.0,
                18.0,
                84.0,
                "WGS 84 / UTM zone 33N",
                "UTM zona 33N, usato in Italia meridionale, Adriatico e Sud (es. Calabria/Puglia).",
            ),
            "EPSG:3857": (
                -180,
                -85,
                180,
                85,
                "Web Mercator",
                "Usato da Google Maps/OSM. Le tue coordinate sembrano pronte per il web.",
            ),
            "EPSG:4326": (
                -180,
                -90,
                180,
                90,
                "WGS 84 (Gradi)",
                "Coordinate geografiche standard. Ideale per GPS e dati globali.",
            ),
        }

    def set_language(self, language):
        self.language = normalize_language(language)

    def tr(self, key, **kwargs):
        return text(key, self.language, **kwargs)

    def deep_scan(self, layer, manual_query=""):
        """
        Esegue una ricerca su Nominatim OSM, interroga Wikipedia e testa le
        coordinate contro oltre 120 EPSG mondiali.
        """
        query_name = None

        if manual_query and manual_query.strip():
            query_name = manual_query.strip()
        else:
            target_fields = [
                "town",
                "città",
                "citta",
                "county",
                "comune",
                "provincia",
                "name",
                "nome",
                "city",
                "location",
                "localita",
                "frazione",
                "toponimo",
                "village",
                "municipality",
                "region",
                "state",
            ]
            field_idx = -1

            for field in layer.fields():
                if field.name().lower() in target_fields:
                    field_idx = layer.fields().indexFromName(field.name())
                    break

            if field_idx != -1:
                for feat in layer.getFeatures():
                    val = feat.attributes()[field_idx]
                    if val and isinstance(val, str) and len(val.strip()) > 2:
                        query_name = val.strip()
                        break

        if not query_name:
            return None

        try:
            encoded_query = urllib.parse.quote(query_name)
            url = (
                "https://nominatim.openstreetmap.org/search"
                f"?q={encoded_query}&format=json&limit=1"
            )

            # Security check for Bandit B310: ensure only http/https schemes
            parsed_url = urllib.parse.urlparse(url)
            if parsed_url.scheme not in ("http", "https"):
                raise ValueError(f"URL scheme {parsed_url.scheme} is not allowed")

            req = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT},
            )
            with urllib.request.urlopen(req, timeout=NETWORK_TIMEOUT_SECONDS) as response:  # nosec B310
                data = json.loads(response.read().decode("utf-8"))
                if not data:
                    return None
                lon = float(data[0]["lon"])
                lat = float(data[0]["lat"])
        except Exception as e:
            QgsMessageLog.logMessage(self.tr("suggest.log_osm", error=e), LOG_TAG, Qgis.Warning)
            return None

        # Ricerca Wikipedia
        wiki_desc = ""
        try:
            wiki_language = "en" if self.language == "en" else "it"
            wiki_url = (
                f"https://{wiki_language}.wikipedia.org/w/api.php"
                "?action=query&prop=extracts&exintro&explaintext"
                f"&titles={encoded_query}&format=json"
            )

            # Security check for Bandit B310: ensure only http/https schemes
            parsed_wiki_url = urllib.parse.urlparse(wiki_url)
            if parsed_wiki_url.scheme not in ("http", "https"):
                raise ValueError(f"URL scheme {parsed_wiki_url.scheme} is not allowed")

            wiki_req = urllib.request.Request(
                wiki_url,
                headers={"User-Agent": USER_AGENT},
            )
            with urllib.request.urlopen(wiki_req, timeout=NETWORK_TIMEOUT_SECONDS) as wiki_response:  # nosec B310
                wiki_data = json.loads(wiki_response.read().decode("utf-8"))
                pages = wiki_data.get("query", {}).get("pages", {})
                for page_id, page_info in pages.items():
                    if "extract" in page_info and page_info["extract"]:
                        wiki_desc = page_info["extract"][:200] + "..."
                        break
        except Exception as e:
            QgsMessageLog.logMessage(self.tr("suggest.log_wikipedia", error=e), LOG_TAG, Qgis.Warning)

        point_wgs84 = QgsPointXY(lon, lat)
        src_crs = QgsCoordinateReferenceSystem("EPSG:4326")

        epsg_candidates = [3857, 3003, 3004] + list(range(32601, 32661)) + list(range(32701, 32761))
        layer_center = layer.extent().center()

        valid_epsgs = []
        is_crs_valid = layer.crs().isValid()

        for epsg in epsg_candidates:
            dest_crs = QgsCoordinateReferenceSystem(f"EPSG:{epsg}")
            if not dest_crs.isValid():
                continue

            try:
                transform = QgsCoordinateTransform(src_crs, dest_crs, QgsProject.instance())
                proj_point = transform.transform(point_wgs84)

                # Calcola la distanza tra il punto calcolato da OSM e il centro
                # del layer
                dx = proj_point.x() - layer_center.x()
                dy = proj_point.y() - layer_center.y()
                dist = math.sqrt(dx**2 + dy**2)

                valid_epsgs.append(
                    {
                        "epsg": epsg,
                        "dist": dist,
                        "name": dest_crs.description(),
                    }
                )
            except Exception:
                continue

        if valid_epsgs:
            valid_epsgs.sort(key=lambda x: x["dist"])
            options = []
            for i, v in enumerate(valid_epsgs[:5]):  # Prendi i migliori 5
                match_pct = 100 if i == 0 else max(10, int(100 - (v["dist"] / 2000)))
                dist_km = int(v["dist"] / 1000)

                options.append(
                    {
                        "id": f"EPSG:{v['epsg']}",
                        "name": f"Match {match_pct}% - EPSG:{v['epsg']} ({v['name']})",
                        "reason": self.tr("suggest.deep_distance", dist_km=dist_km),
                    }
                )

            wiki_text = self.tr("suggest.wikipedia_info", desc=wiki_desc) if wiki_desc else ""
            alert_msg = ""

            cond1 = "UTM zone 32N" in options[0]["name"] and "Calabria" in query_name.title()
            cond2 = valid_epsgs[0]["dist"] > 20000

            # Controllo se è un file probabilmente disegnato nel fuso sbagliato
            if not is_crs_valid:
                epsg_val = valid_epsgs[0]["epsg"]
                dist_km = int(valid_epsgs[0]["dist"] / 1000)
                alert_msg = self.tr("suggest.deep_alert_no_crs", epsg=epsg_val, dist_km=dist_km)
            elif cond1 or cond2:
                dist_km = int(valid_epsgs[0]["dist"] / 1000)
                alert_msg = self.tr("suggest.deep_alert_mismatch", dist_km=dist_km)

            best_epsg = valid_epsgs[0]["epsg"]
            reason = self.tr("suggest.deep_reason", query=query_name, epsg=best_epsg)
            return {
                "id": options[0]["id"],
                "name": options[0]["name"],
                "reason": f"{reason}{wiki_text}{alert_msg}",
                "options": options,
            }

        return None

    def suggest_crs(self, layer):
        """
        Analizza l'extent e restituisce un dict con auth_id, nome e spiegazione.
        """
        extent = layer.extent()
        center = extent.center()

        # 1. Check se sono Gradi (WGS84)
        if abs(extent.xMaximum()) <= 180 and abs(extent.yMaximum()) <= 90:
            return {
                "id": "EPSG:4326",
                "name": self.tr("suggest.wgs84_degrees.name"),
                "reason": self.tr("suggest.wgs84_degrees.reason"),
            }

        x = center.x()
        y = center.y()

        # Le coordinate in UTM per l'Italia (sia 32N che 33N) hanno X
        # tipicamente tra 300.000 e 800.000 e Y (Northing) tra 4.000.000
        # (Sud Italia) e 5.300.000 (Nord Italia).
        if 300000 < x < 800000 and 4000000 < y < 5300000:
            # Siamo in UTM. Come decidiamo tra 32 e 33?
            # In UTM, la Falsa Origine (X=500.000) è il meridiano centrale.
            # E' difficile distinguere 32 da 33 solo dai metri "grezzi" se
            # non sappiamo a quale parallelo corrispondono, ma statisticamente
            # Calabria e Sud/Est Italia usano spesso UTM 33N.
            # Per una stima rozza (se consideriamo coordinate standard senza
            # falso est specificato in fase di rilievo):

            # Cerchiamo di dedurlo dall'estensione se possibile, altrimenti
            # diamo un default sensato.
            # Se siamo molto a sud (Y bassa), per la Calabria/Puglia è più
            # probabile 33N.
            if y < 4500000:  # Circa a sud di Roma
                return {
                    "id": "EPSG:32633",
                    "name": "WGS 84 / UTM zone 33N",
                    "reason": self.tr("suggest.wgs84_utm33.reason"),
                }
            else:
                return {
                    "id": "EPSG:32632",
                    "name": "WGS 84 / UTM zone 32N",
                    "reason": self.tr("suggest.wgs84_utm32.reason"),
                }

        # Esempio Italia Gauss-Boaga (Fuso Ovest - 3003 e Fuso Est - 3004)
        # Ovest: X ha un falso Est di 1.500.000 -> X varia tra ~1.300.000 e
        # 1.800.000
        if 1300000 < x < 1800000 and 4000000 < y < 5300000:
            return {
                "id": "EPSG:3003",
                "name": self.tr("suggest.gauss_boaga_west.name"),
                "reason": self.tr("suggest.gauss_boaga_west.reason"),
            }

        # Est: X ha un falso Est di 2.520.000 -> X varia tra ~2.300.000 e
        # 2.800.000
        if 2300000 < x < 2800000 and 4000000 < y < 5300000:
            return {
                "id": "EPSG:3004",
                "name": self.tr("suggest.gauss_boaga_east.name"),
                "reason": self.tr("suggest.gauss_boaga_east.reason"),
            }

        # Coordinate Web Mercator (EPSG:3857) per l'Italia sono circa:
        # X: 700.000 - 2.100.000, ma la Y è molto più alta: 4.300.000 -
        # 5.900.000
        if y > 5300000 or (x < 1300000 and y > 4000000):
            return {
                "id": "EPSG:3857",
                "name": "Web Mercator",
                "reason": self.tr("suggest.web_mercator.reason"),
            }

        # Default fallback
        return {
            "id": "EPSG:3857",
            "name": self.tr("suggest.web_mercator.default_name"),
            "reason": self.tr("suggest.web_mercator_default.reason"),
        }
