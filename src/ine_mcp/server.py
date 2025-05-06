import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP
import httpx

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


async def make_ine_request(urlBase: str, language: str, function: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
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
    url = None
    if input_str and params:
        url = f"{urlBase}/{language}/{function}/{input_str}?{params.pop("Id", None)}"
    elif not input_str and not params:
        url = f"{urlBase}/{language}/{function}"
    elif not input_str and params:
        url = f"{urlBase}/{language}/{function}?{params.pop("Id", None)}"
    elif input_str and not params:
        url = f"{urlBase}/{language}/{function}/{input_str}"

    logger.info(f"Requesting INE API: {url}, params: {params}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            # Handle encoding properly
            response.encoding = 'utf-8'
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"INE API error: {str(e)}")
            raise

# -------------------MCP TOOLS-------------------

@mcp.tool() #OK
async def get_ine_data(language: str, function: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Realiza una petición a la API del INE.

    Args:
        language (str): puede ser ES o EN.
        function (str): Funciones implementadas en la API del INE para hacer consultas. Son las siguientes:
            DATOS_TABLA: Obtener datos para una tabla específica.
            DATOS_SERIE: Obtener datos para una serie específica.
            DATOS_METADATAOPERACION: Obtener datos de series pertenecientes a una operación dada utilizando un filtro.
            OPERACIONES_DISPONIBLES: Obtener todas las operaciones disponibles.
            OPERACION: Obtener una operación.
            VARIABLES: Obtener todas las variables disponibles.
            VARIABLES_OPERACION: Obtener todas las variables utilizadas en una operación dada.
            VALORES_VARIABLE: Obtener todos los valores para una variable específica.
            VALORES_VARIABLEOPERACION: Obtener todos los valores para una variable específica de una operación dada.
            TABLAS_OPERACION: Obtener un listado de todas las tablas de una operación.
            GRUPOS_TABLA: Obtener todos los grupos para una tabla específica. Una tabla está definida por diferentes grupos o combos de selección y cada uno de ellos por los valores que toman una o varias variables.
            VALORES_GRUPOSTABLA: Obtener todos los valores de un grupo específico para una tabla dada. Una tabla está definida por diferentes grupos o combos de selección y cada uno de ellos por los valores que toman una o varias variables.
            SERIE: Obtener una serie específica.
            SERIES_OPERACION: Obtener todas las series de una operación.
            VALORES_SERIE: Obtener los valores y variables que definen una serie.
            SERIES_TABLA: Obtener todas las series de una tabla específica.
            SERIE_METADATAOPERACION: Obtener series pertenecientes a una operación dada utilizando un filtro.
            PERIODICIDADES: Obtener las periodicidades disponibles.
            PUBLICACIONES: Obtener las publicaciones disponibles.

        input_str (str): Identificadores de los elementos de entrada de las funciones. Los inputs varían en base a la función utilizada.
        params (dict): Los parámetros en la URL se establecen a partir del símbolo ?. Cuando haya más de un parámetro, el símbolo & se utiliza como separador. No todas las funciones admiten todos los parámetros posibles.

    Returns:
        dict (JSON): Respuesta JSON de la API
    """

    logger.info(f"get_ine_data, input_str: {input_str}")
    logger.info(f"get_ine_data, params: {params}")

    return await make_ine_request(INE_API_URL_BASE, language, function, input_str, params)


@mcp.tool() # DATOS_TABLA OK
async def get_table_data(language: str, input_str: str, params: Optional[dict] = None) -> dict:
    """
    Obtener datos para una tabla específica.

    Args:
        language (str): puede ser ES o EN.
        input_str (str): Código identificativo de la tabla. Para obtener el código de una tabla usar la mcp tool get_publications.
        params (dict): Pueden ser los siguientes
            nult: devolver los n últimos datos o periodos.
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos son 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (‘A’), incluir metadatos (‘M’) o ambos (‘AM’)¨.
            tv: parámetro para filtrar, utilizado con el formato tv=id_variable:id_valor. Más información en https://www.ine.es/dyngs/DAB/index.htm?cid=1102.

    Returns:
        dict (JSON): Información y datos de las series contenidas en la tabla: nombre de la serie, identificador Tempu3 de la unidad, identificador Tempus3 de la escala, fecha, identificador Tempus3 del tipo de dato, identificador Tempus3 del periodo, año y valor (dato).
    """

    return await make_ine_request(INE_API_URL_BASE_cache, language, "DATOS_TABLA", input_str, params)

@mcp.tool() # DATOS_SERIE
async def get_series_data(language: str, input_str: str, params: Optional[dict] = None) -> dict:
    """
    Obtener datos para una serie específica.

    Args:
        language (str): puede ser ES o EN.
        input_str (str): Código identificativo de la serie. Para obtener el código de una serie usar la mcp tool get_publications.
        params (dict): Pueden ser los siguientes
            nult: devolver los n últimos datos o periodos.
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos son 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (‘A’), incluir metadatos (‘M’) o ambos (‘AM’)¨.
            date: obtener los datos entre dos fechas. El formato es date=aaaammdd:aaaammdd.

    Returns:
        dict (JSON): Información de la serie: nombre de la serie, identificador Tempu3 de la unidad, identificador Tempus3 de la escala, fecha, identificador Tempus3 del tipo de dato, identificador Tempus3 del periodo, año y valor (dato).
    """

    return await make_ine_request(INE_API_URL_BASE_cache, language, "DATOS_SERIE", input_str, params)

@mcp.tool() # DATOS_METADATAOPERACION
async def get_series_metadata_operation(language: str, input_str: str, params: Optional[dict] = None) -> dict:
    """
    Obtener datos de series pertenecientes a una operación dada utilizando un filtro.

    Args:
        language (str): puede ser ES o EN.
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

@mcp.tool() #OPERACIONES_DISPONIBLES OK
async def get_available_operations(language: str, params: Optional[dict] = None) -> dict:
    """
    Obtener todas las operaciones disponibles en la API del INE.

    Args:
        language (str): puede ser ES o EN.
        params (dict): Pueden ser los siguientes
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.
            geo: para obtener resultados en función del ámbito geográfico:
            geo=1: resultados por comunidades autónomas, provincias, municipios y otras desagregaciones.
            geo=0: resultados nacionales.
            page: la respuesta está paginada. Se ofrece un máximo de 500 elementos por página para no ralentizar la respuesta. Para consultar las páginas siguientes, se utiliza el parámetro page.

    Returns:
        dict (JSON): Se obtienen los identificadores del elemento operación estadística. Existen tres códigos para la identificación de la operación estadística "Índice de Precios de Consumo (IPC)":
            código numérico Tempus3 interno (Id=25).
            código de la operación estadística en el Inventario de Operaciones Estadísticas (IOE30138).
            código alfabético Tempus3 interno (IPC).
    """
    input=None

    return await make_ine_request(INE_API_URL_BASE, language, "OPERACIONES_DISPONIBLES", input, params)

@mcp.tool() #OPERACION OK
async def get_operation(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener una operación disponible en la API del INE.

    Args:
        language (str): puede ser ES o EN.
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

@mcp.tool() #VARIABLES OK
async def get_variables(language: str, params: Optional[dict] = None) -> dict:
    """
    Obtener todas las variables disponibles.

    Args:
        language (str): puede ser ES o EN.
        params (dict): Pueden ser los siguientes
            page: la respuesta está paginada. Se ofrece un máximo de 500 elementos por página para no ralentizar la respuesta. Para consultar las páginas siguientes, se utiliza el parámetro page.
    Returns:
        dict (JSON): Información de todas las variables del Sistema: identificador Tempus3, nombre de la variable y código oficial.
    """
    input=None

    return await make_ine_request(INE_API_URL_BASE, language, "VARIABLES", input, params)

@mcp.tool() #VARIABLES_OPERACION OK
async def get_variables_operation(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener todas las variables utilizadas en una operación dada.

    Args:
        language (str): puede ser ES o EN.
        input_str (str): Código identificativo de la operación. Para consultar las operaciones disponibles usar la mcp tool get_available_operations
        params (dict): Pueden ser los siguientes
            page: la respuesta está paginada. Se ofrece un máximo de 500 elementos por página para no ralentizar la respuesta. Para consultar las páginas siguientes, se utiliza el parámetro page.
    Returns:
        dict (JSON): Información de las variables que describen la operación: identificador Tempus3, nombre de la variable y código oficial.
    """

    return await make_ine_request(INE_API_URL_BASE, language, "VARIABLES_OPERACION", input_str, params)

@mcp.tool() #VALORES_VARIABLE OK
async def get_variables_values(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener todos los valores para una variable específica.

    Args:
        language (str): puede ser ES o EN.
        input_str (str): Código identificador de la variable. Para consultar las variables disponibles usar la mcp tool get_variables
        params (dict): Pueden ser los siguientes
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.
    Returns:
        dict (JSON): Información de los valores que puede tomar la variable: identificador Tempus3 del valor, identificador Tempus 3 de la variable a la que pertenece, nombre del valor y código oficial.
    """

    return await make_ine_request(INE_API_URL_BASE, language, "VALORES_VARIABLE", input_str, params)

@mcp.tool() #VALORES_VARIABLEOPERACION OK
async def get_variable_values_operation(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener todos los valores para una variable específica de una operación dada.

    Args:
        language (str): puede ser ES o EN.
        input_str (str): Códigos identificadores de la variable y de la operación. Para consultar las operaciones disponibles usar la mcp tool get_available_operations y para consultar las variables disponibles usar la mcp tool get_variables
        params (dict): Pueden ser los siguientes
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.
    Returns:
        dict (JSON): Información de los valores que puede tomar la variable para describir la operación: identificador Tempus3 del valor, objeto variable Tempus3 a la que pertenece, nombre del valor y código oficial.
    """

    return await make_ine_request(INE_API_URL_BASE, language, "VALORES_VARIABLEOPERACION", input_str, params)

@mcp.tool() #TABLAS_OPERACION OK
async def get_operation_tables(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener un listado de todas las tablas de una operación disponible en la API del INE.

    Args:
        language (str): puede ser ES o EN.
        Input (str): Código identificativo de la operación. Para consultar las operaciones disponibles usar la mcp tool get_available_operations
        params (dict): Pueden ser los siguientes
            det: nivel de detalle de la información mostrada. Valores válidos: 0, 1 y 2.
            geo: para obtener resultados en función del ámbito geográfico.
                geo=1: resultados por comunidades autónomas, provincias, municipios y otras desagregaciones.
                geo=0: Resultados nacionales.
                tip: obtener la respuesta de las peticiones de modo más amigable (`A’).
            
    Returns:
        dict (JSON): Información de las tablas asociadas a la operación: identificador Tempus3 de la tabla, nombre de la tabla, código con información del nivel geográfico y clasificación, objeto Tempus3 periodicidad, objeto Tempus3 publicación, objeto Tempus3 periodo inicio, año inicio, PubFechaAct dentro de la publicación , FechaRef_fin y última modificación.
            FechaRef_fin: nulo cuando el último periodo publicado coincide con el de la publicación fecha, en otro caso, cuando la tabla está cortada en un periodo anterior al de la publicación fecha, es sustituido por Fk_perido_fin/ Anyo_perido_fin (fecha del último dato publicado). Consultar https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/33.
            PubFechaAct = contiene la última fecha de actualización de la tabla y el último periodo-año publicado.
    """

    return await make_ine_request(INE_API_URL_BASE, language, "TABLAS_OPERACION", input_str, params)

@mcp.tool() #GRUPOS_TABLA OK
async def get_table_groups(language: str, input_str: Optional[str] = None) -> dict:
    """
    Obtener todos los grupos para una tabla específica. Una tabla está definida por diferentes grupos o combos de selección y cada uno de ellos por los valores que toman una o varias variables.

    Args:
        language (str): puede ser ES o EN.
        input_str (str): Código identificativo de la tabla. Para obtener el código de una tabla usar la mcp tool get_publications.

    Returns:
        dict (JSON): Grupos de valores que definen la tabla: identificador Tempus3 del grupo y nombre del grupo.
    """
    params=None

    return await make_ine_request(INE_API_URL_BASE, language, "GRUPOS_TABLA", input_str, params)

@mcp.tool() #VALORES_GRUPOSTABLA OK
async def get_values_tables_groups(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener todos los valores de un grupo específico para una tabla dada. Una tabla está definida por diferentes grupos o combos de selección y cada uno de ellos por los valores que toman una o varias variables.

    Args:
        language (str): puede ser ES o EN.
        Input (str): Códigos identificativos de la tabla y del grupo. Para consultar los grupos de una tabla usar la mcp tool get_table_groups
        params (dict): Pueden ser los siguientes
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.
            
    Returns:
        dict (JSON): Información de los valores pertenecientes al grupo: identificador Tempus3 del valor, identificador Tempus 3 de la variable a la que pertenece, nombre del valor y código oficial.
    """
    return await make_ine_request(INE_API_URL_BASE, language, "VALORES_GRUPOSTABLA", input_str, params)

@mcp.tool() #SERIE OK
async def get_series(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener una serie específica.

    Args:
        language (str): puede ser ES o EN.
        Input (str): Código identificativo de la serie. Para obtener el código de una serie usar la mcp tool get_publications.
        params (dict): Pueden ser los siguientes
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (`A´), incluir metadatos (`M´) o ambos (`AM´).
            
    Returns:
        dict (JSON): Información de la serie: identificadores Tempus3 de la serie, objeto Tempus3 operación, nombre de la serie, número de decimales que se van a visualizar para los datos de esa serie, objeto Tempus3 periodicidad, objeto Tempus3 publicación, PubFechaAct dentro de la publicación, objeto Tempsu3 clasificación, objeto Tempus3 escala y objeto Tempus3 unidad.
        PubFechaAct = contiene la última fecha de actualización de la serie y el último periodo-año publicado.
        clasificación = nos da información de la versión temporal de la serie, por ejemplo, la clasificación nacional que en algunos casos sigue, marco poblacional, base utilizada en el cálculo de los índices,...
    """
    return await make_ine_request(INE_API_URL_BASE, language, "SERIE", input_str, params)

@mcp.tool() #SERIES_OPERACION OK
async def get_series_operation(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
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

@mcp.tool() #VALORES_SERIE OK
async def get_series_values(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener los valores y variables que definen una serie.

    Args:
        language (str): puede ser ES o EN.
        Input (str): Código identificativo de la serie. Para obtener el código de una serie usar la mcp tool get_publications.
        params (dict). Pueden ser los siguientes:
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.

    Returns:
        dict (JSON): Información de los metadatos que definen a la serie: identificador Tempus3 del valor, identificador Tempus3 de la variable a la que pertenece, nombre del valor y código oficial del valor.
    """
    return await make_ine_request(INE_API_URL_BASE, language, "VALORES_SERIE", input_str, params)

@mcp.tool() #SERIES_TABLA OK
async def get_series_tables(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener todas las series de una tabla específica.

    Args:
        language (str): puede ser ES o EN.
        Input (str): Código identificativo de la serie. Para obtener el código de una serie usar la mcp tool get_publications.
        params (dict). Pueden ser los siguientes:
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos del parámetro: 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (`A´), incluir metadatos (`M´) o ambos (`AM´).
            tv: parámetro para filtrar, utilizado con el formato tv=id_variable:id_valor. Más información en Como filtrar datos de una tabla.
    Returns:
        dict (JSON): Información de las series de la tabla: identificadores Tempus3 de la serie, identificador Tempus3 de la operación, nombre de la serie, número de decimales que se van a visualizar para los datos de esa serie, identificador Tempus3 de la periodicidad, identificador Tempus3 de la publicación, identificador Tempsu3 de la clasificación, identificador Tempus3 de la escala e identificador Tempus3 de la unidad.
    """
    return await make_ine_request(INE_API_URL_BASE, language, "SERIES_TABLA", input_str, params)

@mcp.tool() #SERISERIE_METADATAOPERACIONES_TABLA OK
async def get_series_metadata_operations(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener series pertenecientes a una operación dada utilizando un filtro.

    Args:
        language (str): puede ser ES o EN.
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

@mcp.tool() #PERIODICIDADES OK
async def get_periodicities(language: str) -> dict:
    """
    Obtener las periodicidades disponibles.

    Args:
        language (str): puede ser ES o EN.
        
    Returns:
        dict (JSON): Información de las periodicidades disponibles: identificador Tempus3 de la periodicidad, nombre y código.
    """

    input_str = None
    params = None
    return await make_ine_request(INE_API_URL_BASE, language, "PERIODICIDADES", input_str, params)

@mcp.tool() #PUBLICACIONES OK
async def get_publications(language: str, params: Optional[dict] = None) -> dict:
    """
    Obtener las publicaciones disponibles.

    Args:
        language (str): puede ser ES o EN.
        params (dict). Pueden ser los siguientes:
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos son 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (‘A’).
    
    Returns:
        dict (JSON): Información de todas las publicaciones: identificador Tempus3 de la publicación, nombre, identificador Tempus3 de la periodicidad e identificador Tempus3 de la publicación fecha.
    """
    input_str=None
    return await make_ine_request(INE_API_URL_BASE, language, "PUBLICACIONES", input_str, params)

@mcp.tool() #PUBLICACIONES_OPERACION OK
async def get_publications_operation(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener todas las publicaciones para una operación dada.

    Args:
        language (str): puede ser ES o EN.
        Input (str): Código identificativo de la operación. Para consultar las operaciones disponibles usar la mcp tool get_available_operations
        params (dict). Pueden ser los siguientes:
            det: ofrece mayor nivel de detalle de la información mostrada. Valores válidos son 0, 1 y 2.
            tip: obtener la respuesta de las peticiones de modo más amigable (‘A’).
    
    Returns:
        dict (JSON): Información de todas las publicaciones de una operación: identificador Tempus3 de la publicación, nombre, identificador Tempus3 de la periodicidad e identificador Tempus3 de la publicación fecha.
    """
    return await make_ine_request(INE_API_URL_BASE, language, "PUBLICACIONES_OPERACION", input_str, params)

@mcp.tool() #PUBLICACIONFECHA_PUBLICACION OK
async def get_publication_date(language: str, input_str: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """
    Obtener las fechas de publicación para una publicación dada.

    Args:
        language (str): puede ser ES o EN.
        Input (str): Código identificativo de la publicación. Para obtener una lista de las publicaciones usar la mcp tool get_publications o a get_publications_operation
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