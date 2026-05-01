import urllib.request
import urllib.parse
import json
import math
from qgis.core import QgsCoordinateReferenceSystem, QgsPointXY, QgsCoordinateTransform, QgsProject


class SmartSuggest:
    def __init__(self, iface):
        self.iface = iface
        # Database semplificato di EPSG comuni e i loro bounding box (WGS84)
        # Formato: 'EPSG': (xmin, ymin, xmax, ymax, "Nome", "Perché")
        self.crs_db = {
            'EPSG:3003': (6.62, 36.4, 13.14, 47.05, "Monte Mario / Italy zone 1", "Standard per la cartografia tecnica in Italia Ovest."),
            'EPSG:3004': (12.45, 36.4, 18.48, 47.05, "Monte Mario / Italy zone 2", "Standard per la cartografia tecnica in Italia Est."),
            'EPSG:32632': (6.0, 0.0, 12.0, 84.0, "WGS 84 / UTM zone 32N", "Sistema globale preciso, molto usato in Europa centrale e Italia."),
            'EPSG:32633': (12.0, 0.0, 18.0, 84.0, "WGS 84 / UTM zone 33N", "UTM zona 33N, usato in Italia meridionale, Adriatico e Sud (es. Calabria/Puglia)."),
            'EPSG:3857': (-180, -85, 180, 85, "Web Mercator", "Usato da Google Maps/OSM. Le tue coordinate sembrano pronte per il web."),
            'EPSG:4326': (-180, -90, 180, 90, "WGS 84 (Gradi)", "Coordinate geografiche standard. Ideale per GPS e dati globali.")
        }

    def deep_scan(self, layer, manual_query=""):
        """
        Esegue una ricerca su Nominatim OSM usando i campi testuali del layer (o la query manuale),
        interroga Wikipedia e testa matematicamente le coordinate contro oltre 120 EPSG mondiali,
        restituendo i candidati migliori.
        """
        query_name = None

        if manual_query and manual_query.strip():
            query_name = manual_query.strip()
        else:
            target_fields = [
                'town',
                'città',
                'citta',
                'county',
                'comune',
                'provincia',
                'name',
                'nome',
                'city',
                'location',
                'localita',
                'frazione',
                'toponimo',
                'village',
                'municipality',
                'region',
                'state']
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
            url = f"https://nominatim.openstreetmap.org/search?q={
                urllib.parse.quote(query_name)}&format=json&limit=1"
            req = urllib.request.Request(
                url, headers={
                    'User-Agent': 'QGIS-QuickCRSFixer-Plugin'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                if not data:
                    return None
                lon = float(data[0]['lon'])
                lat = float(data[0]['lat'])
        except Exception as e:
            print(f"Errore OSM: {e}")
            return None

        # Ricerca Wikipedia
        wiki_desc = ""
        try:
            wiki_url = f"https://it.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={
                urllib.parse.quote(query_name)}&format=json"
            wiki_req = urllib.request.Request(
                wiki_url, headers={
                    'User-Agent': 'QGIS-QuickCRSFixer-Plugin'})
            with urllib.request.urlopen(wiki_req) as wiki_response:
                wiki_data = json.loads(wiki_response.read().decode('utf-8'))
                pages = wiki_data.get('query', {}).get('pages', {})
                for page_id, page_info in pages.items():
                    if 'extract' in page_info and page_info['extract']:
                        wiki_desc = page_info['extract'][:200] + "..."
                        break
        except Exception as e:
            print(f"Errore Wikipedia: {e}")

        point_wgs84 = QgsPointXY(lon, lat)
        src_crs = QgsCoordinateReferenceSystem("EPSG:4326")

        # Aggiungiamo anche EPSG catastali generici se necessario, ma i fusi
        # principali sono questi.
        epsg_candidates = [3857, 3003, 3004] + \
            list(range(32601, 32661)) + list(range(32701, 32761))
        layer_center = layer.extent().center()

        valid_epsgs = []
        is_crs_valid = layer.crs().isValid()

        for epsg in epsg_candidates:
            dest_crs = QgsCoordinateReferenceSystem(f"EPSG:{epsg}")
            if not dest_crs.isValid():
                continue

            try:
                transform = QgsCoordinateTransform(
                    src_crs, dest_crs, QgsProject.instance())
                proj_point = transform.transform(point_wgs84)

                # Calcola la distanza tra il punto calcolato da OSM e il centro
                # del layer
                dist = math.sqrt((proj_point.x() - layer_center.x())
                                 ** 2 + (proj_point.y() - layer_center.y())**2)

                valid_epsgs.append(
                    {'epsg': epsg, 'dist': dist, 'name': dest_crs.description()})
            except BaseException:
                continue

        if valid_epsgs:
            valid_epsgs.sort(key=lambda x: x['dist'])
            options = []
            for i, v in enumerate(valid_epsgs[:5]):  # Prendi i migliori 5
                match_pct = 100 if i == 0 else max(
                    10, int(100 - (v['dist'] / 2000)))

                options.append({
                    'id': f"EPSG:{v['epsg']}",
                    'name': f"Match {match_pct}% - EPSG:{v['epsg']} ({v['name']})",
                    'reason': f"Distanza: {int(v['dist'] / 1000)}km dal centro teorico."
                })

            wiki_text = f"<br><br><b style='color:#2D89EF'>Info Wikipedia:</b> <i>{wiki_desc}</i>" if wiki_desc else ""
            alert_msg = ""

            # Controllo se è un file probabilmente disegnato nel fuso sbagliato
            if not is_crs_valid:
                alert_msg = f"<br><br><b style='color:#ff8c00;'>ATTENZIONE:</b> Il file non possiede alcun Sistema di Riferimento nativo (es. manca il file .prj). La ricerca ha determinato matematicamente che l'<b>EPSG:{
                    valid_epsgs[0]['epsg']}</b> è il più probabile (distanza dal centro teorico {
                    int(
                        valid_epsgs[0]['dist'] /
                        1000)}km). Applicalo usando il tasto 'Assign' in basso."
            elif "UTM zone 32N" in options[0]['name'] and "Calabria" in query_name.title() or valid_epsgs[0]['dist'] > 20000:
                alert_msg = f"<br><br><b style='color:#ff8c00;'>ATTENZIONE:</b> Il sistema di riferimento potrebbe non coincidere con la reale posizione geografica (distanza dal centro {
                    int(
                        valid_epsgs[0]['dist'] /
                        1000)}km). Il file potrebbe essere stato esportato in un fuso diverso dal suo originale. Assegna l'EPSG calcolato e poi riproietta tramite gli strumenti di QGIS (o dal menu a tendina)."

            return {
                'id': options[0]['id'],
                'name': options[0]['name'],
                'reason': f"Ricerca per <b>{query_name}</b> completata! Ti suggerisco l'uso di <b>EPSG:{valid_epsgs[0]['epsg']}</b>.{wiki_text}{alert_msg}",
                'options': options}

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
                'id': 'EPSG:4326',
                'name': "WGS 84 (Gradi)",
                'reason': "Le coordinate sono piccole (gradi), tipiche del WGS84."}

        x = center.x()
        y = center.y()

        # Le coordinate in UTM per l'Italia (sia 32N che 33N) hanno X tipicamente tra 300.000 e 800.000
        # e Y (Northing) tra 4.000.000 (Sud Italia) e 5.300.000 (Nord Italia).
        if 300000 < x < 800000 and 4000000 < y < 5300000:
            # Siamo in UTM. Come decidiamo tra 32 e 33?
            # In UTM, la Falsa Origine (X=500.000) è il meridiano centrale.
            # E' difficile distinguere 32 da 33 solo dai metri "grezzi" se non sappiamo a quale parallelo corrispondono,
            # ma statisticamente, se un utente lavora in Calabria e ha coordinate UTM senza "False Northing/Easting" strane:
            # Per una stima rozza (se consideriamo coordinate standard senza
            # falso est specificato in fase di rilievo):

            # Tuttavia, a livello pratico per il Sud/Est Italia si usa molto la 33N.
            # Cerchiamo di dedurlo dall'estensione se possibile, altrimenti diamo un default sensato.
            # Se siamo molto a sud (Y bassa), per la Calabria/Puglia è più
            # probabile 33N.
            if y < 4500000:  # Circa a sud di Roma
                return {
                    'id': 'EPSG:32633',
                    'name': "WGS 84 / UTM zone 33N",
                    'reason': "Coordinate UTM in area compatibile con Sud Italia/Adriatico (es. Calabria/Puglia)."
                }
            else:
                return {
                    'id': 'EPSG:32632',
                    'name': "WGS 84 / UTM zone 32N",
                    'reason': "Coordinate UTM in area compatibile con Nord/Centro Italia."}

        # Esempio Italia Gauss-Boaga (Fuso Ovest - 3003 e Fuso Est - 3004)
        # Ovest: X ha un falso Est di 1.500.000 -> X varia tra ~1.300.000 e
        # 1.800.000
        if 1300000 < x < 1800000 and 4000000 < y < 5300000:
            return {
                'id': 'EPSG:3003',
                'name': "Monte Mario / Italy zone 1 (Ovest)",
                'reason': "I numeri e il 'Falso Est' di 1.5M indicano Gauss-Boaga Ovest."}

        # Est: X ha un falso Est di 2.520.000 -> X varia tra ~2.300.000 e
        # 2.800.000
        if 2300000 < x < 2800000 and 4000000 < y < 5300000:
            return {
                'id': 'EPSG:3004',
                'name': "Monte Mario / Italy zone 2 (Est)",
                'reason': "I numeri e il 'Falso Est' di 2.52M indicano Gauss-Boaga Est."}

        # Coordinate Web Mercator (EPSG:3857) per l'Italia sono circa:
        # X: 700.000 - 2.100.000, ma la Y è molto più alta: 4.300.000 -
        # 5.900.000
        if y > 5300000 or (x < 1300000 and y > 4000000):
            return {
                'id': 'EPSG:3857',
                'name': "Web Mercator",
                'reason': "Le coordinate (specialmente la Y alta) suggeriscono Web Mercator."}

        # Default fallback
        return {
            'id': 'EPSG:3857',
            'name': "Web Mercator (Default)",
            'reason': "Valori in metri non riconosciuti in zone UTM/Gauss-Boaga note, ipotizzo Web Mercator."
        }
