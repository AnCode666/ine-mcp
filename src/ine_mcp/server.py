import logging
from typing import Optional, List, Dict
from mcp.server.fastmcp import FastMCP
import httpx
import re
import difflib

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "ine-mcp",
    description="MCP server for querying the INE API (Spanish National Statistics Institute)"
)

# Constants
INE_API_URL_BASE = "https://servicios.ine.es/wstempus/js"
INE_API_URL_BASE_cache = "https://servicios.ine.es/wstempus/jsCache"

async def make_ine_request(
        urlBase: str,
        language: str,
        function: str,
        input_str: Optional[str] = None,
        params: Optional[dict] = None) -> dict:
    """
    Realiza una petición a la API del INE.

    Args:
        Los Args entre llaves { } son obligatorios. Los Args entre corchetes [ ] opcionales y cambian en relación a la función usada.
        {language}. Puede ser ES (español), o EN (inglés)
        {function}. Funciones del sistema para poder realizar diferentes tipos de consulta.
        {input}. Identificadores de los elementos de entrada de las funciones. Los inputs varían en base a la función utilizada.
        [params]. Los parámetros en la URL se establecen a partir del símbolo ?. Cuando haya más de un parámetro, el símbolo & se utiliza como separador. No todas las funciones admiten todos los parámetros posibles.

    Returns:
        dict: Respuesta JSON de la API.
    """
    # Construcción correcta de URL según docs INE:
    # https://servicios.ine.es/wstempus/js/{idioma}/{función}/{input}[?parámetros]
    if input_str and params:
        url = f"{urlBase}/{language}/{function}/{input_str}?{params.pop('Id', None)}"
    elif not input_str and not params:
        url = f"{urlBase}/{language}/{function}"
    elif not input_str and params:
        url = f"{urlBase}/{language}/{function}?{params.pop('Id', None)}"
    elif input_str and not params:
        url = f"{urlBase}/{language}/{function}/{input_str}"
    else:
        raise ValueError("URL mal construida.")

    logger.info(f"Requesting INE API: {url}, params: {params}")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"INE API error: {str(e)}")
            raise

def filter_dict_by_nombre(
    jsonDataFromAPI: Dict,
    terms: List[str],
    use_regex: bool = False,
    use_fuzzy: bool = False,
    fuzzy_threshold: float = 0.7
) -> List[Dict]:
    """
    Filtra operaciones, publicaciones, tablas, etc por coincidencias en "Nombre" usando prioridad:
    regex > fuzzy > substring.

    Args:
        jsonDataFromAPI (List[Dict]): Lista de operaciones, publicaciones, tablas, etc del INE.
        terms (List[str]): Palabras clave o patrones.
        use_regex (bool): Prioriza regex.
        use_fuzzy (bool): Luego fuzzy matching si regex no activa.
        fuzzy_threshold (float): Ratio mínimo para fuzzy.

    Returns:
        List[Dict]: Coincidencias únicas.
    """
    matched_ids = set()
    result = []

    for op in jsonDataFromAPI:
        nombre = op.get("Nombre", "")
        for term in terms:
            matched = False

            if use_regex:
                if re.search(term, nombre, re.IGNORECASE):
                    matched = True

            elif use_fuzzy:
                ratio = difflib.SequenceMatcher(None, term.lower(), nombre.lower()).ratio()
                if ratio >= fuzzy_threshold:
                    matched = True

            else:
                if term.lower() in nombre.lower():
                    matched = True

            if matched and op["Id"] not in matched_ids:
                matched_ids.add(op["Id"])
                result.append(op)
                break

    return result

# -------------------MCP API TOOLS-------------------

#INEbase / Lista completa de operaciones
#Tempus3 / Lista completa de publicaciones

@mcp.tool()
async def get_DATOS_TABLA(language: str, input_str: str, params: Optional[dict] = None) -> dict:
    """
    Obtener datos para una tabla específica.

    Args:
        language (str): ES o EN.
        input_str (str): Código identificativo de la tabla. Para obtenerlo usar la mcp tool get_and_filter_PUBLICACIONES.
        params (dict): Pueden ser los siguientes
            nult: devolver los n últimos datos o periodos.
            det: nivel de detalle de la información. 0, 1 ó 2.
            tip: obtener la respuesta de modo más amigable (‘A’), incluir metadatos (‘M’) o ambos (‘AM’)¨.
            tv: parámetro para filtrar, utilizado con el formato tv=id_variable:id_valor. Más información en https://www.ine.es/dyngs/DAB/index.htm?cid=1102.

    Returns:
        dict (JSON): Información y datos de las series contenidas en la tabla: nombre de la serie, identificador Tempu3 de la unidad, identificador Tempus3 de la escala, fecha, identificador Tempus3 del tipo de dato, identificador Tempus3 del periodo, año y valor (dato).
    """

    return await make_ine_request(INE_API_URL_BASE_cache, language, "DATOS_TABLA", input_str, params)

@mcp.tool()
async def get_DATOS_SERIE(language: str, input_str: str, params: Optional[dict] = None) -> dict:
    """
    Obtener datos para una serie específica.

    Args:
        language (str): ES o EN.
        input_str (str): Código identificativo de la serie. Para obtenerlo usar la mcp tool get_and_filter_PUBLICACIONES.
        params (dict): Pueden ser los siguientes
            nult: devolver los n últimos datos o periodos.
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos son 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (‘A’), incluir metadatos (‘M’) o ambos (‘AM’)¨.
            date: obtener los datos entre dos fechas. El formato es date=aaaammdd:aaaammdd.

    Returns:
        dict (JSON): Información de la serie: nombre de la serie, identificador Tempu3 de la unidad, identificador Tempus3 de la escala, fecha, identificador Tempus3 del tipo de dato, identificador Tempus3 del periodo, año y valor (dato).
    """

    return await make_ine_request(INE_API_URL_BASE_cache, language, "DATOS_SERIE", input_str, params)

@mcp.tool()
async def get_DATOS_METADATAOPERACION(language: str, input_str: str, params: Optional[dict] = None) -> dict:
    """
    Obtener datos de series pertenecientes a una operación dada utilizando un filtro.

    Args:
        language (str): ES o EN.
        input_str (str): Código identificativo de la operación. Para consultar las operaciones disponibles usar la mcp tool get_available_operations
        params (dict): Pueden ser los siguientes:
            p: id de la periodicidad de las series. Periodicidades comunes: 1 (mensual), 3 (trimestral), 6 (semestral), 12 (anual). Para ver una lista de las periodicidades acceder a PERIODICIDADES.
            nult: devolver los n últimos datos o periodos.
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos son 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (‘A’), incluir metadatos (‘M’) o ambos (‘AM’).
            g1: primer filtro de variables y valores. El formato es g1=id_variable_1:id_valor_1. Cuando no se especifica el id_valor_1 se devuelven todos los valores de id_variable_1 (g1=id_variable_1:). Para obtener las variables de una operación dada consultar https://servicios.ine.es/wstempus/js/ES/VARIABLES_OPERACION/IPC. Para obtener los valores de una variable específica de una operación data consultar https://servicios.ine.es/wstempus/js/ES/VALORES_VARIABLEOPERACION/762/IPC.
            g2: segundo filtro de variables y valores. El formato es g2=id_variable_2:id_valor_2. Cuando no se especifica el id_valor_2 se devuelven todos los valores de id_variable_2 (g2=id_variable_2:). Seguiríamos con g3, g4,… según el número de filtros que se utilicen sobre variables.

    Returns:
        dict (JSON): Los datods de las series solicitados.
    """

    return await make_ine_request(INE_API_URL_BASE, language, "DATOS_METADATAOPERACION", input_str, params)

@mcp.tool() #Ejecutar de primera
async def get_and_filter_OPERACIONES_DISPONIBLES(
    language: str,
    params: Optional[dict] = None,
    search_terms: Optional[List[str]] = None,
    use_regex: bool = False
) -> dict:
    """
    Obtener todas las operaciones disponibles en la API del INE, con posibilidad de filtrarlas.

    Args:
        language (str): ES o EN.
        params (dict): Pueden ser los siguientes:
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.
            geo: para obtener resultados en función del ámbito geográfico:
            geo=1: resultados por comunidades autónomas, provincias, municipios y otras desagregaciones.
            geo=0: resultados nacionales.
            page: la respuesta está paginada. Se ofrece un máximo de 500 elementos por página para no ralentizar la respuesta. Para consultar las páginas siguientes, se utiliza el parámetro page.
        search_terms (List[str], optional): Lista de palabras clave o patrones a buscar.
        use_regex (bool): Si True, activa búsqueda por expresión regular.

    Returns:
        dict (JSON): Diccionario con todas las operaciones y las filtradas (si aplica). Existen tres códigos para la identificación de la operación estadística "Índice de Precios de Consumo (IPC)":
            código numérico Tempus3 interno (Id=25).
            código de la operación estadística en el Inventario de Operaciones Estadísticas (IOE30138).
            código alfabético Tempus3 interno (IPC).
    """
    input = None
    operaciones = await make_ine_request(INE_API_URL_BASE, language, "OPERACIONES_DISPONIBLES", input, params)

    if search_terms:
        filtradas = filter_dict_by_nombre(operaciones, search_terms, use_regex)
        return {"operaciones filtradas": filtradas}
    else:
        #filtradas = []
        return {"operaciones": operaciones}

@mcp.tool()
async def get_OPERACION(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener una operación disponible en la API del INE.

    Args:
        language (str): ES o EN.
        input_str (str): Código identificativo de la operación. Para consultar las operaciones disponibles usar la mcp tool get_available_operations
        params (dict): Pueden ser los siguientes
            det: nivel de detalle de la información mostrada. Valores válidos: 0, 1 y 2.
            
    Returns:
        dict (JSON): Información de la operación estadística IPC: identificador Tempus3, código del IOE y nombre de la operación. Existen tres códigos para la identificación de la operación estadística "Índice de Precios de Consumo (IPC)":
            1.código numérico Tempus3 interno (Id=25).
            2.código de la operación estadística en el Inventario de Operaciones Estadísticas (IOE30138).
            3.código alfabético Tempus3 interno (IPC).
    """

    return await make_ine_request(INE_API_URL_BASE, language, "OPERACION", input_str, params)

@mcp.tool()
async def get_VARIABLES(language: str, params: Optional[dict] = None) -> dict:
    """
    Obtener todas las variables disponibles.

    Args:
        language (str): ES o EN.
        params (dict): Pueden ser los siguientes
            page: la respuesta está paginada. Se ofrece un máximo de 500 elementos por página para no ralentizar la respuesta. Para consultar las páginas siguientes, se utiliza el parámetro page.
    Returns:
        dict (JSON): Información de todas las variables del Sistema: identificador Tempus3, nombre de la variable y código oficial.
    """
    input=None

    return await make_ine_request(INE_API_URL_BASE, language, "VARIABLES", input, params)

@mcp.tool()
async def get_VARIABLES_OPERACION(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener todas las variables utilizadas en una operación dada.

    Args:
        language (str): ES o EN.
        input_str (str): Código identificativo de la operación. Para consultar las operaciones disponibles usar la mcp tool get_available_operations
        params (dict): Pueden ser los siguientes
            page: la respuesta está paginada. Se ofrece un máximo de 500 elementos por página para no ralentizar la respuesta. Para consultar las páginas siguientes, se utiliza el parámetro page.
    Returns:
        dict (JSON): Información de las variables que describen la operación: identificador Tempus3, nombre de la variable y código oficial.
    """

    return await make_ine_request(INE_API_URL_BASE, language, "VARIABLES_OPERACION", input_str, params)

@mcp.tool()
async def get_VALORES_VARIABLE(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener todos los valores para una variable específica.

    Args:
        language (str): ES o EN.
        input_str (str): Código identificador de la variable. Para consultar las variables disponibles usar la mcp tool get_variables
        params (dict): Pueden ser los siguientes
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.
    Returns:
        dict (JSON): Información de los valores que puede tomar la variable: identificador Tempus3 del valor, identificador Tempus 3 de la variable a la que pertenece, nombre del valor y código oficial.
    """

    return await make_ine_request(INE_API_URL_BASE, language, "VALORES_VARIABLE", input_str, params)

@mcp.tool()
async def get_VALORES_VARIABLEOPERACION(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener todos los valores para una variable específica de una operación dada.

    Args:
        language (str): ES o EN.
        input_str (str): Códigos identificadores de la variable y de la operación. Para consultar las operaciones disponibles usar la mcp tool get_available_operations y para consultar las variables disponibles usar la mcp tool get_variables
        params (dict): Pueden ser los siguientes
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.
    Returns:
        dict (JSON): Información de los valores que puede tomar la variable para describir la operación: identificador Tempus3 del valor, objeto variable Tempus3 a la que pertenece, nombre del valor y código oficial.
    """

    return await make_ine_request(INE_API_URL_BASE, language, "VALORES_VARIABLEOPERACION", input_str, params)

@mcp.tool()
async def get_and_filter_TABLAS_OPERACION(
    language: str, 
    input_str: Optional[str] = None, 
    params: Optional[dict] = None,
    search_terms: Optional[List[str]] = None,
    use_regex: bool = False
) -> dict:
    """
    Obtener un listado de todas las tablas de una operación disponible en la API del INE, con posibilidad de filtrarlas.

    Args:
        language (str): ES o EN.
        Input (str): Código identificativo de la operación. Para consultar las operaciones disponibles usar la mcp tool get_available_operations
        params (dict): Pueden ser los siguientes
            det: nivel de detalle de la información mostrada. Valores válidos: 0, 1 y 2.
            geo: para obtener resultados en función del ámbito geográfico.
                geo=1: resultados por comunidades autónomas, provincias, municipios y otras desagregaciones.
                geo=0: Resultados nacionales.
                tip: obtener la respuesta de las peticiones de modo más amigable (`A’).
        search_terms (List[str], optional): Lista de palabras clave o patrones a buscar.
        use_regex (bool): Si True, activa búsqueda por expresión regular.
            
    Returns:
        dict (JSON): Diccionario con todas las tablas y las filtradas (si aplica): identificador Tempus3 de la tabla, nombre de la tabla, código con información del nivel geográfico y clasificación, objeto Tempus3 periodicidad, objeto Tempus3 publicación, objeto Tempus3 periodo inicio, año inicio, PubFechaAct dentro de la publicación , FechaRef_fin y última modificación.
            FechaRef_fin: nulo cuando el último periodo publicado coincide con el de la publicación fecha, en otro caso, cuando la tabla está cortada en un periodo anterior al de la publicación fecha, es sustituido por Fk_perido_fin/ Anyo_perido_fin (fecha del último dato publicado). Consultar https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/33.
            PubFechaAct = contiene la última fecha de actualización de la tabla y el último periodo-año publicado.
    """

    tablas = await make_ine_request(INE_API_URL_BASE, language, "TABLAS_OPERACION", input_str, params)

    if search_terms:
        filtradas = filter_dict_by_nombre(tablas, search_terms, use_regex)
        return {"tablas filtradas": filtradas}
    else:
        #filtradas = []
        return {"tablas": tablas}

@mcp.tool()
async def get_GRUPOS_TABLA(language: str, input_str: Optional[str] = None) -> dict:
    """
    Obtener todos los grupos para una tabla específica. Una tabla está definida por diferentes grupos o combos de selección y cada uno de ellos por los valores que toman una o varias variables.

    Args:
        language (str): ES o EN.
        input_str (str): Código identificativo de la tabla. Para obtener el código de una tabla usar la mcp tool get_and_filter_PUBLICACIONES.

    Returns:
        dict (JSON): Grupos de valores que definen la tabla: identificador Tempus3 del grupo y nombre del grupo.
    """
    params=None

    return await make_ine_request(INE_API_URL_BASE, language, "GRUPOS_TABLA", input_str, params)

@mcp.tool()
async def get_VALORES_GRUPOSTABLA(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener todos los valores de un grupo específico para una tabla dada. Una tabla está definida por diferentes grupos o combos de selección y cada uno de ellos por los valores que toman una o varias variables.

    Args:
        language (str): ES o EN.
        Input (str): Códigos identificativos de la tabla y del grupo. Para consultar los grupos de una tabla usar la mcp tool get_table_groups
        params (dict): Pueden ser los siguientes
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.
            
    Returns:
        dict (JSON): Información de los valores pertenecientes al grupo: identificador Tempus3 del valor, identificador Tempus 3 de la variable a la que pertenece, nombre del valor y código oficial.
    """
    return await make_ine_request(INE_API_URL_BASE, language, "VALORES_GRUPOSTABLA", input_str, params)

@mcp.tool()
async def get_SERIE(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener una serie específica.

    Args:
        language (str): ES o EN.
        Input (str): Código identificativo de la serie. Para obtener el código de una serie usar la mcp tool get_and_filter_PUBLICACIONES.
        params (dict): Pueden ser los siguientes
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (`A´), incluir metadatos (`M´) o ambos (`AM´).
            
    Returns:
        dict (JSON): Información de la serie: identificadores Tempus3 de la serie, objeto Tempus3 operación, nombre de la serie, número de decimales que se van a visualizar para los datos de esa serie, objeto Tempus3 periodicidad, objeto Tempus3 publicación, PubFechaAct dentro de la publicación, objeto Tempsu3 clasificación, objeto Tempus3 escala y objeto Tempus3 unidad.
        PubFechaAct = contiene la última fecha de actualización de la serie y el último periodo-año publicado.
        clasificación = nos da información de la versión temporal de la serie, por ejemplo, la clasificación nacional que en algunos casos sigue, marco poblacional, base utilizada en el cálculo de los índices,...
    """
    return await make_ine_request(INE_API_URL_BASE, language, "SERIE", input_str, params)

@mcp.tool()
async def get_SERIES_OPERACION(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener todas las series de una operación.

    Args:
        language (str): puede ser ES o EN.
        Input (str): Código identificativo de la operación. Para consultar las operaciones disponibles usar la mcp tool get_available_operations
        params (dict). Pueden ser los siguientes:
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (`A´), incluir metadatos (`M´) o ambos (`AM´).
            page: la respuesta está paginada. Se ofrece un máximo de 500 elementos por página para no ralentizar la respuesta. Para consultar las páginas siguientes, se utiliza el parámetro page.
            
    Returns:
        dict (JSON): Información de las series: identificadores Tempus3 de la serie, identificador Tempus3 de la operación, nombre de la serie, número de decimales que se van a visualizar para los datos de esa serie, identificador Tempus3 de la periodicidad, identificador Tempus3 de la publicación, identificador Tempsu3 de la clasificación, identificador Tempus3 de la escala e identificador Tempus3 de la unidad.
    """
    return await make_ine_request(INE_API_URL_BASE, language, "SERIES_OPERACION", input_str, params)

@mcp.tool()
async def get_VALORES_SERIE(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener los valores y variables que definen una serie.

    Args:
        language (str): ES o EN.
        Input (str): Código identificativo de la serie. Para obtener el código de una serie usar la mcp tool get_and_filter_PUBLICACIONES.
        params (dict). Pueden ser los siguientes:
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.

    Returns:
        dict (JSON): Información de los metadatos que definen a la serie: identificador Tempus3 del valor, identificador Tempus3 de la variable a la que pertenece, nombre del valor y código oficial del valor.
    """
    return await make_ine_request(INE_API_URL_BASE, language, "VALORES_SERIE", input_str, params)

@mcp.tool()
async def get_SERIES_TABLA(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener todas las series de una tabla específica.

    Args:
        language (str): ES o EN.
        Input (str): Código identificativo de la serie. Para obtener el código de una serie usar la mcp tool get_and_filter_PUBLICACIONES.
        params (dict). Pueden ser los siguientes:
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (`A´), incluir metadatos (`M´) o ambos (`AM´).
            tv: parámetro para filtrar, utilizado con el formato tv=id_variable:id_valor. Más información en Como filtrar datos de una tabla.
    Returns:
        dict (JSON): Información de las series de la tabla: identificadores Tempus3 de la serie, identificador Tempus3 de la operación, nombre de la serie, número de decimales que se van a visualizar para los datos de esa serie, identificador Tempus3 de la periodicidad, identificador Tempus3 de la publicación, identificador Tempsu3 de la clasificación, identificador Tempus3 de la escala e identificador Tempus3 de la unidad.
    """
    return await make_ine_request(INE_API_URL_BASE, language, "SERIES_TABLA", input_str, params)

@mcp.tool()
async def get_SERIE_METADATAOPERACION(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener series pertenecientes a una operación dada utilizando un filtro.

    Args:
        language (str): ES o EN.
        Input (str): Código identificativo de la operación. Para consultar las operaciones disponibles usar la mcp tool get_available_operations
        params (dict). Pueden ser los siguientes:
            p: id de la periodicidad de las series. Periodicidades comunes: 1 (mensual), 3 (trimestral), 6 (semestral), 12 (anual). Para ver una lista de las periodicidades acceder a PERIODICIDADES.
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos son 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (‘A’), incluir metadatos (‘M’) o ambos (‘AM’).
            g1: primer filtro de variables y valores. El formato es g1=id_variable_1:id_valor_1. Cuando no se especifica el id_valor_1 se devuelven todos los valores de id_variable_1 (g1=id_variable_1:). Para obtener las variables de una operación dada consultar https://servicios.ine.es/wstempus/js/ES/VARIABLES_OPERACION/IPC. Para obtener los valores de una variable específica de una operación data consultar https://servicios.ine.es/wstempus/js/ES/VALORES_VARIABLEOPERACION/762/IPC.
            g2: segundo filtro de variables y valores. El formato es g2=id_variable_2:id_valor_2. Cuando no se especifica el id_valor_2 se devuelven todos los valores de id_variable_2 (g2=id_variable_2:). Seguiríamos con g3, g4,… según el número de filtros que se utilicen sobre variables.
    
    Returns:
        dict (JSON): Información de las series cuya definición de metadatos cumple los criterios establecidos: identificadores Tempus3 de la serie, identificador Tempus3 de la operación, nombre de la serie, número de decimales que se van a visualizar para los datos de esa serie, identificador Tempus3 de la periodicidad, identificador Tempus3 de la publicación, identificador Tempsu3 de la clasificación, identificador Tempus3 de la escala e identificador Tempus3 de la unidad.
    """
    return await make_ine_request(INE_API_URL_BASE, language, "SERIE_METADATAOPERACION", input_str, params)

@mcp.tool()
async def get_PERIODICIDADES(language: str) -> dict:
    """
    Obtener las periodicidades disponibles.

    Args:
        language (str): ES o EN.
        
    Returns:
        dict (JSON): Información de las periodicidades disponibles: identificador Tempus3 de la periodicidad, nombre y código.
    """

    input_str = None
    params = None
    return await make_ine_request(INE_API_URL_BASE, language, "PERIODICIDADES", input_str, params)

@mcp.tool()
async def get_and_filter_PUBLICACIONES(
    language: str,
    params: Optional[dict] = None,
    search_terms: Optional[List[str]] = None,
    use_regex: bool = False
) -> dict:
    """
    Obtener todas las publicaciones disponibles en la API del INE, con posibilidad de filtrarlas.

    Args:
        language (str): ES o EN.
        params (dict). Pueden ser los siguientes:
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos son 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (‘A’).
        search_terms (List[str], optional): Lista de palabras clave o patrones a buscar.
        use_regex (bool): Si True, activa búsqueda por expresión regular.

    Returns:
        dict (JSON): Información de todas las publicaciones y las filtradas (si aplica): identificador Tempus3 de la publicación, nombre, identificador Tempus3 de la periodicidad e identificador Tempus3 de la publicación fecha.
    """
    input = None
    publicaciones = await make_ine_request(INE_API_URL_BASE, language, "PUBLICACIONES", input, params)

    if search_terms:
        filtradas = filter_dict_by_nombre(publicaciones, search_terms, use_regex)
        return {"publicaciones filtradas": filtradas}
    else:
        #filtradas = []
        return {"publicaciones": publicaciones}

@mcp.tool()
async def get_PUBLICACIONES_OPERACION(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener todas las publicaciones para una operación dada.

    Args:
        language (str): ES o EN.
        Input (str): Código identificativo de la operación. Para consultar las operaciones disponibles usar la mcp tool get_available_operations
        params (dict). Pueden ser los siguientes:
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos son 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (‘A’).
    
    Returns:
        dict (JSON): Información de todas las publicaciones de una operación: identificador Tempus3 de la publicación, nombre, identificador Tempus3 de la periodicidad e identificador Tempus3 de la publicación fecha.
    """
    return await make_ine_request(INE_API_URL_BASE, language, "PUBLICACIONES_OPERACION", input_str, params)

@mcp.tool()
async def get_PUBLICACIONFECHA_PUBLICACION(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener las fechas de publicación para una publicación dada.

    Args:
        language (str): ES o EN.
        Input (str): Código identificativo de la publicación. Para obtener una lista de las publicaciones usar las mcp tools get_and_filter_PUBLICACIONES y get_and_filter_PUBLICACIONES_operation
        params (dict). Pueden ser los siguientes:
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos son 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (‘A’).
    
    Returns:
        dict (JSON): Información de todas las publicaciones de una operación: identificador Tempus3 de la publicación, nombre, identificador Tempus3 de la periodicidad e identificador Tempus3 de la publicación fecha.
    """
    return await make_ine_request(INE_API_URL_BASE, language, "PUBLICACIONFECHA_PUBLICACION", input_str, params)

# Main function
def main():
    """Arrancar el servidor mcp"""
    mcp.run()

if __name__ == "__main__":
    mcp.run()