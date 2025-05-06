[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-yellow.svg)](README_es.md)

# INE-MCP. Integración vía MCP con la API del INE

**INE es el Instituto Nacional de Estadística de España.**

**INE-mcp** permite acceder a datos estadísticos oficiales de España directamente desde Claude AI y otros clientes MCP compatibles, utilizando el protocolo **Model Context Protocol (MCP)**.

INE-mcp es un servidor MCP que expone herramientas para que los LLM puedan consultar indicadores económicos, demográficos y sociales del INE.

## Características principales

- Consulta de **indicadores económicos** (PIB, IPC, desempleo, etc.)
- Acceso a **datos demográficos** (censo, migraciones, natalidad)
- Series temporales históricas de datos estadísticos
- Metadatos de operaciones estadísticas oficiales
- Filtrado por territorio, periodo y variables específicas
- Respuestas estructuradas en formato JSON

## Instalación

### Instalar desde uv

### Prerrequisitos

- Python 3.10 o superior.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager.

### Instalación de uv

Lo primero que hay que hacer es instalar `uv`, que es un gestor de paquetes para Python.
**Se instala desde la consola**.

En MAC y Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

En Windows:

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

También se puede instalar con pip:

```bash
pip install uv
```

Para más información sobre la instalación de **uv**, consulta la [documentación oficial](https://docs.astral.sh/uv/getting-started/installation/).

## Integración con clientes como Claude para Escritorio

Una vez que tenemos **uv** instalado, ya podemos usar el servidor MCP desde cualquier cliente compatible, como Claude para Escritorio, en cuyo caso los pasos a seguir son los siguientes:

1. Ve a **Claude > Settings > Developer > Edit Config > `claude_desktop_config.json`**.
2. Agrega el siguiente bloque de código dentro de `"mcpServers"`:

```json
"ine_mcp": {
    "command": "uvx",
    "args": [
        "ine_mcp"
    ]
}   
```

3. Consultar la documentación oficial del INE: <https://www.ine.es/dyngs/DAB/index.htm?cid=1099>
4. Si ya tienes otro servidor MCP configurado en tu cliente, separa cada servidor con una coma `,`.

En general, para integrarlo en cualquier otro cliente compatible con MCP, como pueden ser Cursor, CODEGPT o Roo Code, solamente hay que ir a la correspondiente configuración de los servidores MCP del cliente y añadir el mismo bloque de código.

## Ejemplos de uso

Una vez configurado correctamente, podrás pedirle cosas como:

```
- `"¿Qué datos del INE de España puedes consultar?"`
- `"Busca datos de la Encuesta de Población Activa (EPA)"`
- `"Dime los índices de precios de productos siderúrgicos durante el primer trimestre del año 2023"`
---
