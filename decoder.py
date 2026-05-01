import base64
import binascii
import logging
from typing import Optional

import geopandas as gpd
import polyline
from shapely import wkb, wkt
from shapely.geometry.base import BaseGeometry
from shapely.errors import WKBReadingError, WKTReadingError

# Configurazione logging per debug avanzato in produzione
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger("GeoDecoder")


def attempt_decode_geometry(payload: str) -> Optional[BaseGeometry]:
    """
    Tenta di decodificare una stringa sconosciuta nei formati GIS più comuni.
    Ritorna un oggetto Shapely BaseGeometry se il parsing ha successo, altrimenti None.
    """
    # 1. Pulizia base del payload (rimozione spazi, che potrebbero rompere
    # Base64 o Hex)
    clean_payload = payload.replace(" ", "").replace("\n", "")

    # 2. Tentativo come WKT (Well-Known Text) standard
    try:
        geom = wkt.loads(payload)
        logger.info("Decodifica completata tramite WKT.")
        return geom
    except (WKTReadingError, Exception) as e:
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
    except (binascii.Error, WKBReadingError, Exception) as e:
        logger.debug(f"Fallito parsing Hex WKB: {e}")

    # 5. Tentativo come WKB codificato in Base64
    try:
        binary_data = base64.b64decode(clean_payload, validate=True)
        geom = wkb.loads(binary_data)
        logger.info("Decodifica completata tramite Base64 WKB.")
        return geom
    except (binascii.Error, WKBReadingError, Exception) as e:
        logger.debug(f"Fallito parsing Base64 WKB: {e}")

    logger.error(
        "Impossibile decodificare il payload con i formati standard conosciuti.")
    return None


def process_unknown_payload(
    payload: str,
     output_file: str = "output_debug.gpkg") -> None:
    """
    Processa il payload e, in caso di successo, salva il risultato in un GeoPackage
    pronto per l'ingestion in QGIS.
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
    f"Dato vettoriale esportato con successo in: {output_file}")
        except Exception as e:
            logger.error(f"Errore durante l'esportazione del GeoPackage: {e}")
    else:
        logger.warning(
            "Nessuna geometria esportabile. Verificare l'encoding originario.")


if __name__ == "__main__":
    # Test esecuzione con il payload fornito
    mistery_payload = "1AV0*}z 1AR' 1A2w-%g PAlxzU PA0L PADGr 1A^) 1Avq 1AH. 1ATt${ PALb PA(1 1A$J{? PA<, 1A2U0 1A c 1A6< 1A^) PA(\\ 1A^K PAp_ 1AV} PAH%ur 1ADio PA\\K 1ANb PA<, 1A\\ Ay PA(~ PA`2U 1Ap_ `T2g 1A&u 1A8gD PA`TR 1A<N PAxz PAL7 lVQI 1A\\ A 1Afff 1A@5^ PA\\m PAlxz 1A8gD 1A(\\ PA$lxj ,C\\_ PAHP 1A\\ A PA\\K PADGr 1A>W[ PAl+ PAhff PAth 1A`TR 1AV} PAPI PA|6 QI!^ 1Ax-! PAtq 1A\\ A1- 1ATt$W 1A(~ PA8gD PAhff PA$(~ PAho PA@5^ PA8EG PA`) <,$B _v7/ PA$J{ PA`) PAd] PAx-! 1Afffz PAlV} PAp_ PAHr z6+x PA\\d; 8EOg 1ADio 1An4 PA4^ 1A0L 1A433;* PA`vOn 1AhDi[ 1A|?5 PAT' 1ATt$ PAd; PATR'` |?uz 1At$ 1AH. PA(\\ PA|a2e F%Ef 1AlV}vj PA|?5 PA@` 1ARI 1AHr \\m]$ PA0L PA`) 1AV0* PAX[ PA$J{ PA$J{ PA433 1Ab2U 1AX9 1Avq 1A&1 PA(S PAd] 1A>W[ PAH%u PA(: 1A^K 1AL7 1Ajo 1AzX PA433 PAH. 1Ajo PAH. 1Ap_ 1AJY PAL7 PA0n PA0w- 1A@5^ 1A`vO PAPI PAPI 1AlV} PA<N 1AlV} PA4U0 1AJY 1AlV}V PAHr 1A6< PA`) 1A c PA\\d; PA(S 1A@5^6 PA|6 1Ax-! PA|6 1A433W PA|6 PA`vO. PA`vO PAp= 1Ad] PAx-! PA`vO^ PAlV} PA|?5 PA\\d;_ 1Ad] lV=y 1A<, lV]W PAD> 1A6< PA`) 1A\\m 1AF%u 1A,e 1Ap_ PAp_ PA|?5^) PA`vO PAlV} :p^% 1AR' PAhffV~ 1Arh PA|6 PAx-! PA\\m PAlM 1A8gDU PAL{ 1A8gD 1AV0* 1A A 1A$(~ PA`2U@ 1AN@ 1Avq 1AHP 1AHP 1AB` 1AB` 1A~j 1A~j PA0n PAtF PA|6 1A<, PA\\ A PA<N 1AJY 1A$(~ 1ADio PA@W[ ~j4p PA@W[ ~jt| PA0n PA0n PAL7 PA0n 1A.! PA@W[ 1A&1 PAl+ 1A.! PA@` PA0w- PAP@ PA0w- PAP@ PADio@ PAP@ rhA< PA@W[ PA0n 1AX[ 1A0* 1At$ 1A*: _vS> o_3Y o_'^ 8Esy PA8EG 1ATt$ PAH. |a"4): ". 1A&S `T" < 1Ad] PAH % uBI 1Ad] PA(\ PA(\ PA8< 1Az6 1A(\ .nC$ PA,! 1A`vOr 1A8EG2 PAT' 1A`vO2 1A8EG 1A@5^ 1A2U0R& PAlxz 1A2U0RB PAlxzEA 9#RS 1A,e 1Ajo 1A&u PAxO PAho 9#RP 1A,e PAhff 1Ajo PATt$g PA`TR 1AR' PA(: 1AN@ 1A<N PAPk 1A.n PAl+ 1AzX PAl+ 1Arh PALb A`QS 1AFGr +eqe PAHP 1A|a2Q PA(~ PAT' PADGr PAD> PA4^ PA4^ 1AX9 1A.! PAlV}^ PAxz 1AV0*}z"
    process_unknown_payload(mistery_payload)
