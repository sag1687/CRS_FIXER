"""Small internal translation table for the plugin UI and user messages."""

DEFAULT_LANGUAGE = "it"
SUPPORTED_LANGUAGES = ("it", "en")

TRANSLATIONS = {
    "action.cancelled": {
        "it": "Operazione annullata dall'utente.",
        "en": "Operation cancelled by the user.",
    },
    "action.cancelled.title": {"it": "Annullato", "en": "Cancelled"},
    "action.fix_applied": {
        "it": "Fix applicato a {layer} e salvato in {file_name}",
        "en": "Fix applied to {layer} and saved to {file_name}",
    },
    "action.fix_error": {
        "it": "Impossibile applicare il fix: {error}",
        "en": "Unable to apply the fix: {error}",
    },
    "action.fixed_count": {
        "it": "Corretti {count} layer in memoria.",
        "en": "Fixed {count} layers in memory.",
    },
    "action.save_title": {
        "it": "Salva risultato in GeoPackage",
        "en": "Save result as GeoPackage",
    },
    "action.success": {"it": "Successo", "en": "Success"},
    "button.assign.tooltip": {
        "it": "Assegna il CRS corretto senza trasformare le coordinate.",
        "en": "Assign the correct CRS without transforming coordinates.",
    },
    "button.assign": {"it": "Assegna", "en": "Assign"},
    "button.deep_scan.tooltip": {
        "it": (
            "Cerca toponimi e confronta EPSG candidati tramite servizi "
            "esterni."),
        "en": (
            "Search place names and compare candidate EPSG codes using "
            "external services."),
    },
    "button.deep_scan": {"it": "Deep Scan OSM", "en": "Deep Scan OSM"},
    "button.fix_all.tooltip": {
        "it": (
            "Applica automaticamente il CRS suggerito a tutti i layer "
            "segnalati."),
        "en": "Automatically apply the suggested CRS to all flagged layers.",
    },
    "button.fix_all": {"it": "Correggi Tutto", "en": "Fix All"},
    "button.refresh": {"it": "Aggiorna", "en": "Refresh"},
    "button.refresh.tooltip": {
        "it": "Analizza di nuovo i layer caricati nel progetto.",
        "en": "Scan the loaded project layers again.",
    },
    "button.reproject": {"it": "Reproject", "en": "Reproject"},
    "button.reproject_resolved": {
        "it": "Riproietta in...",
        "en": "Reproject to...",
    },
    "button.reproject.tooltip": {
        "it": "Crea una copia trasformando le coordinate verso l'EPSG scelto.",
        "en": (
            "Create a copy by transforming coordinates to the selected "
            "EPSG."
        ),
    },
    "deep_scan.error": {
        "it": "Errore durante Deep Scan: {error}",
        "en": "Deep Scan error: {error}",
    },
    "deep_scan.no_result": {
        "it": (
            "Nessun risultato trovato. Prova a inserire un luogo "
            "manualmente."
        ),
        "en": "No result found. Try entering a place name manually.",
    },
    "deep_scan.running": {
        "it": "<i>Ricerca Nominatim/OSM in corso... attendere...</i>",
        "en": "<i>Nominatim/OSM search running... please wait...</i>",
    },
    "deep_scan.select_layer": {
        "it": (
            "<b style='color:#ff8c00;'>Seleziona prima un layer dalla lista "
            "per indicare a chi applicare "
            "l'EPSG individuato!</b>"
        ),
        "en": (
            "<b style='color:#ff8c00;'>Select a layer first so the detected "
            "EPSG can be applied to the "
            "right target.</b>"
        ),
    },
    "deep_scan.success": {"it": "Trovato: {name}", "en": "Found: {name}"},
    "detector.degree_in_projected": {
        "it": "Coordinate in gradi ma CRS proiettato.",
        "en": "Coordinates are in degrees, but the CRS is projected.",
    },
    "detector.invalid_crs": {
        "it": "CRS non definito o invalido.",
        "en": "CRS is undefined or invalid.",
    },
    "detector.meter_in_degree": {
        "it": "Coordinate in metri ma CRS in gradi (WGS84).",
        "en": "Coordinates are in meters, but the CRS is in degrees (WGS84).",
    },
    "detector.waiting": {
        "it": "In attesa di analisi...",
        "en": "Waiting for analysis...",
    },
    "dialog.error": {"it": "Errore", "en": "Error"},
    "fixer.assign_error": {
        "it": "Errore nell'assegnazione CRS: {error}",
        "en": "CRS assignment error: {error}",
    },
    "fixer.reproject_error": {
        "it": "Errore nella riproiezione: {error}",
        "en": "Reprojection error: {error}",
    },
    "info.disclaimer": {
        "it": (
            "<p style='text-align: center; font-size: 11px; color: #a0c4ff;'>"
            "<i>Il plugin richiede una connessione internet attiva.<br>"
            "Deep Scan utilizza servizi esterni per l'analisi "
            "intelligente.</i></p>"
        ),
        "en": (
            "<p style='text-align: center; font-size: 11px; color: #a0c4ff;'>"
            "<i>The plugin requires an active internet connection.<br>"
            "Deep Scan uses external services for intelligent "
            "analysis.</i></p>"
        ),
    },
    "info.osm": {
        "it": (
            "<p style='text-align: center; font-size: 10px; color: #ffffff;'>"
            "<b>OpenStreetMap</b><br>Ricerca Geografica<br>Licenza: ODbL</p>"
        ),
        "en": (
            "<p style='text-align: center; font-size: 10px; color: #ffffff;'>"
            "<b>OpenStreetMap</b><br>Geographic Search<br>License: ODbL</p>"
        ),
    },
    "info.plugins": {
        "it": "<b>Altri Plugin:</b>",
        "en": "<b>Other Plugins:</b>",
    },
    "info.select_plugin": {
        "it": "Seleziona un plugin...",
        "en": "Select a plugin...",
    },
    "info.version": {"it": "Versione", "en": "Version"},
    "info.wiki": {
        "it": (
            "<p style='text-align: center; font-size: 10px; color: #ffffff;'>"
            "<b>Wikipedia</b><br>Informazioni Luoghi<br>Licenza: CC BY-SA</p>"
        ),
        "en": (
            "<p style='text-align: center; font-size: 10px; color: #ffffff;'>"
            "<b>Wikipedia</b><br>Place Information<br>License: CC BY-SA</p>"
        ),
    },
    "label.language": {"it": "Lingua:", "en": "Language:"},
    "message.layer_problem": {
        "it": "Problema CRS rilevato su {layer}",
        "en": "CRS issue detected on {layer}",
    },
    "resolved.details": {
        "it": "<b>{name}</b>: Pronto per la riproiezione finale (opzionale).",
        "en": "<b>{name}</b>: Ready for the optional final reprojection.",
    },
    "resolved.empty_details": {
        "it": "<i>Seleziona un layer sistemato per riproiettarlo...</i>",
        "en": "<i>Select a fixed layer to reproject it...</i>",
    },
    "stats.problems": {
        "it": "<b>Problemi: {count}</b>",
        "en": "<b>Issues: {count}</b>",
    },
    "suggest.deep_alert_mismatch": {
        "it": (
            "<br><br><b style='color:#ff8c00;'>ATTENZIONE:</b> Il sistema di "
            "riferimento potrebbe non "
            "coincidere con la reale posizione geografica (distanza dal "
            "centro {dist_km}km). Il file potrebbe "
            "essere stato esportato in un fuso diverso dal suo originale. "
            "Assegna l'EPSG calcolato e poi "
            "riproietta tramite gli strumenti di QGIS (o dal menu a tendina)."
        ),
        "en": (
            "<br><br><b style='color:#ff8c00;'>WARNING:</b> The reference "
            "system may not match the real "
            "geographic position (distance from center {dist_km}km). The file "
            "may have been exported in a "
            "different zone from its original one. Assign the calculated EPSG "
            "first, then reproject using QGIS "
            "tools or the drop-down menu."
        ),
    },
    "suggest.deep_alert_no_crs": {
        "it": (
            "<br><br><b style='color:#ff8c00;'>ATTENZIONE:</b> Il file non "
            "possiede alcun Sistema di "
            "Riferimento nativo (es. manca il file .prj). La ricerca ha "
            "determinato matematicamente che "
            "l'<b>EPSG:{epsg}</b> e' il piu' probabile (distanza dal centro "
            "teorico {dist_km}km). Applicalo "
            "usando il tasto 'Assign' in basso."
        ),
        "en": (
            "<br><br><b style='color:#ff8c00;'>WARNING:</b> The file has no "
            "native reference system, for "
            "example a missing .prj file. The search mathematically "
            "identified <b>EPSG:{epsg}</b> as the most "
            "likely match (distance from theoretical center {dist_km}km). "
            "Apply it with the 'Assign' button."
        ),
    },
    "suggest.deep_distance": {
        "it": "Distanza: {dist_km}km dal centro teorico.",
        "en": "Distance: {dist_km}km from the theoretical center.",
    },
    "suggest.deep_reason": {
        "it": (
            "Ricerca per <b>{query}</b> completata! Ti suggerisco l'uso di "
            "<b>EPSG:{epsg}</b>."),
        "en": (
            "Search for <b>{query}</b> completed. Suggested CRS: "
            "<b>EPSG:{epsg}</b>."),
    },
    "suggest.gauss_boaga_east.name": {
        "it": "Monte Mario / Italy zone 2 (Est)",
        "en": "Monte Mario / Italy zone 2 (East)",
    },
    "suggest.gauss_boaga_east.reason": {
        "it": "I numeri e il 'Falso Est' di 2.52M indicano Gauss-Boaga Est.",
        "en": "The numbers and 2.52M false easting indicate Gauss-Boaga East.",
    },
    "suggest.gauss_boaga_west.name": {
        "it": "Monte Mario / Italy zone 1 (Ovest)",
        "en": "Monte Mario / Italy zone 1 (West)",
    },
    "suggest.gauss_boaga_west.reason": {
        "it": "I numeri e il 'Falso Est' di 1.5M indicano Gauss-Boaga Ovest.",
        "en": "The numbers and 1.5M false easting indicate Gauss-Boaga West.",
    },
    "suggest.log_osm": {
        "it": "Errore OSM: {error}",
        "en": "OSM error: {error}",
    },
    "suggest.log_wikipedia": {
        "it": "Errore Wikipedia: {error}",
        "en": "Wikipedia error: {error}",
    },
    "suggest.missing": {
        "it": "Nessun suggerimento disponibile.",
        "en": "No suggestion available.",
    },
    "suggest.web_mercator.default_name": {
        "it": "Web Mercator (Default)",
        "en": "Web Mercator (Default)",
    },
    "suggest.web_mercator.reason": {
        "it": (
            "Le coordinate (specialmente la Y alta) suggeriscono Web "
            "Mercator."
        ),
        "en": (
            "The coordinates, especially the high Y value, suggest Web "
            "Mercator."),
    },
    "suggest.web_mercator_default.reason": {
        "it": (
            "Valori in metri non riconosciuti in zone UTM/Gauss-Boaga note, "
            "ipotizzo Web Mercator."),
        "en": (
            "Meter values do not match known UTM/Gauss-Boaga ranges, so Web "
            "Mercator is assumed."),
    },
    "suggest.wikipedia_info": {
        "it": (
            "<br><br><b style='color:#2D89EF'>Info Wikipedia:</b> "
            "<i>{desc}</i>"),
        "en": (
            "<br><br><b style='color:#2D89EF'>Wikipedia info:</b> "
            "<i>{desc}</i>"),
    },
    "suggest.wgs84_degrees.name": {
        "it": "WGS 84 (Gradi)",
        "en": "WGS 84 (Degrees)",
    },
    "suggest.wgs84_degrees.reason": {
        "it": "Le coordinate sono piccole (gradi), tipiche del WGS84.",
        "en": "The coordinates are small degree values, typical of WGS84.",
    },
    "suggest.wgs84_utm32.reason": {
        "it": "Coordinate UTM in area compatibile con Nord/Centro Italia.",
        "en": (
            "UTM coordinates in an area compatible with Northern/Central "
            "Italy."),
    },
    "suggest.wgs84_utm33.reason": {
        "it": (
            "Coordinate UTM in area compatibile con Sud Italia/Adriatico (es. "
            "Calabria/Puglia)."),
        "en": (
            "UTM coordinates in an area compatible with Southern "
            "Italy/Adriatic, such as Calabria/Puglia."),
    },
    "tab.fixer": {"it": "Problemi Rilevati", "en": "Detected Issues"},
    "tab.help": {"it": "Help", "en": "Help"},
    "tab.info": {"it": "Info", "en": "Info"},
    "tab.resolved": {"it": "Riassegna EPSG", "en": "Reassign EPSG"},
    "tree.fixer.col0": {"it": "Layer / Problema", "en": "Layer / Issue"},
    "tree.fixer.col1": {"it": "Suggerimento", "en": "Suggestion"},
    "tree.resolved.col0": {"it": "Layer Sistemato", "en": "Fixed Layer"},
    "tree.resolved.col1": {
        "it": "EPSG Attuale/Suggerito",
        "en": "Current/Suggested EPSG",
    },
    "ui.empty_details": {
        "it": "<i>Seleziona un layer dalla lista per vedere i dettagli...</i>",
        "en": "<i>Select a layer from the list to view details...</i>",
    },
    "valid": {"it": "Valido", "en": "Valid"},
}


def normalize_language(language):
    """Return a supported language code, falling back to Italian."""
    if language in SUPPORTED_LANGUAGES:
        return language
    return DEFAULT_LANGUAGE


def text(key, language=DEFAULT_LANGUAGE, **kwargs):
    """Translate a key and interpolate optional named values."""
    entries = TRANSLATIONS.get(key)
    if not entries:
        return key.format(**kwargs) if kwargs else key
    template = entries.get(
        normalize_language(language), entries[DEFAULT_LANGUAGE]
    )
    return template.format(**kwargs)
