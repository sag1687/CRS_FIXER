import base64
import binascii
import logging
from typing import Optional

import geopandas as gpd
import polyline
from shapely import wkb, wkt
from shapely.errors import ShapelyError
from shapely.geometry.base import BaseGeometry

# Configurazione logging per debug avanzato in produzione
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(name)s] %(message)s",
)
logger = logging.getLogger("GeoDecoder")


def attempt_decode_geometry(payload: str) -> Optional[BaseGeometry]:
    """
    Tenta di decodificare una stringa sconosciuta nei formati GIS più comuni.
    Ritorna un oggetto Shapely BaseGeometry se il parsing ha successo,
    altrimenti None.
    """
    # 1. Pulizia base del payload (rimozione spazi, che potrebbero rompere
    # Base64 o Hex)
    clean_payload = payload.replace(" ", "").replace("\n", "")

    # 2. Tentativo come WKT (Well-Known Text) standard
    try:
        geom = wkt.loads(payload)
        logger.info("Decodifica completata tramite WKT.")
        return geom
    except (ShapelyError, Exception) as e:
        logger.debug(f"Fallito parsing WKT: {e}")

    # 3. Tentativo come Google Encoded Polyline
    try:
        # polyline decodifica in una lista di tuple (lat, lon)
        coords = polyline.decode(payload)
        if coords and len(coords) > 1:
            from shapely.geometry import LineString

            # Inversione lat/lon per lo standard x/y (lon/lat) di
            # Shapely/GeoPandas
            geom = LineString([(lon, lat) for lat, lon in coords])
            logger.info("Decodifica completata tramite Google Polyline.")
            return geom
    except Exception as e:
        logger.debug(f"Fallito parsing Polyline: {e}")

    # 4. Tentativo come WKB (Well-Known Binary) codificato in Hex
    try:
        binary_data = binascii.unhexlify(clean_payload)
        geom = wkb.loads(binary_data)
        logger.info("Decodifica completata tramite Hex WKB.")
        return geom
    except (binascii.Error, ShapelyError, Exception) as e:
        logger.debug(f"Fallito parsing Hex WKB: {e}")

    # 5. Tentativo come WKB codificato in Base64
    try:
        binary_data = base64.b64decode(clean_payload, validate=True)
        geom = wkb.loads(binary_data)
        logger.info("Decodifica completata tramite Base64 WKB.")
        return geom
    except (binascii.Error, ShapelyError, Exception) as e:
        logger.debug(f"Fallito parsing Base64 WKB: {e}")

    logger.error(
        "Impossibile decodificare il payload con i formati standard "
        "conosciuti."
    )
    return None


def process_unknown_payload(
    payload: str, output_file: str = "output_debug.gpkg"
) -> None:
    """
    Processa il payload e, in caso di successo, salva il risultato in un
    GeoPackage pronto per l'ingestion in QGIS.
    """
    geom = attempt_decode_geometry(payload)

    if geom:
        # Costruzione del GeoDataFrame. Si assume WGS84 di default se non
        # specificato.
        gdf = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[geom])
        logger.info(f"Geometria identificata: {geom.geom_type}")

        try:
            # Salvataggio ottimizzato per QGIS
            gdf.to_file(output_file, driver="GPKG")
            logger.info(
                f"Dato vettoriale esportato con successo in: {output_file}"
            )
        except Exception as e:
            logger.error(f"Errore durante l'esportazione del GeoPackage: {e}")
    else:
        logger.warning(
            "Nessuna geometria esportabile. Verificare l'encoding originario."
        )
