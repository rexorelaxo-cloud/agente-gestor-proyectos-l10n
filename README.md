# Agente de gestión de proyectos de localización

Este proyecto implementa un agente simple con LangGraph para consultar información de proyectos de localización.

Los datos son simulados y representan información que podría encontrarse en un sistema de gestión de proyectos, como idiomas, palabras pendientes, estado de revisión y resultados de QA.

El agente utiliza un LLM para decidir cuándo necesita consultar una herramienta y puede realizar varias consultas antes de responder.

## Tecnologías utilizadas

* Python 3.12
* LangChain
* LangGraph
* SQLite
* asyncio

## Herramientas

El agente cuenta con tres herramientas:

* `consultar_proyecto_localizacion`: consulta la información general de un proyecto.
* `consultar_estado_idioma`: consulta el estado de un idioma dentro de un proyecto.
* `consultar_resultados_qa`: consulta los resultados de QA de un idioma.

Las herramientas utilizan datos simulados definidos en `datos_simulados.py`.

## Funcionamiento

El agente utiliza un `StateGraph` basado en `MessagesState`.

El LLM está vinculado a las herramientas mediante `bind_tools()` y decide por sí mismo cuándo utilizarlas.

Una consulta puede requerir más de una llamada a las herramientas antes de generar una respuesta.

Por ejemplo:

> ¿Está listo el proyecto 129171 para entregar en español y francés? Si no, indicame qué falta.

Para responder esta consulta, el agente puede consultar primero el proyecto y después consultar el estado y QA de los idiomas correspondientes.

## Persistencia

Se utiliza SQLite como checkpointer.

Cada conversación tiene un `thread_id`, que permite mantener el contexto de una sesión.

Por ejemplo, después de preguntar:

> ¿Qué idiomas tiene el proyecto 129171?

se puede preguntar:

> ¿Y cuál tiene más palabras pendientes?

utilizando el mismo `thread_id`, y el agente puede utilizar el contexto de la conversación anterior.

También se prueba el uso de diferentes `thread_id` para mantener las conversaciones separadas.

## Instalación

Se requiere Python 3.12 o superior.

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

Crear un archivo `.env` a partir de `.env.example` y agregar la API Key correspondiente.

Por ejemplo:

```text
ANTHROPIC_API_KEY=tu_api_key
```

No incluir la API Key en el repositorio.

## Ejecución

Para ejecutar el agente:

```bash
python main.py
```

El programa ejecuta diferentes casos de prueba, incluyendo:

* una consulta que requiere varias llamadas a herramientas;
* persistencia con `thread_id`;
* separación entre diferentes sesiones;
* manejo de errores;
* uso del límite de recursión.

## Tests

Los tests se pueden ejecutar con:

```bash
pytest
```

Se incluyen tests para las herramientas y para el funcionamiento del grafo.

También se utiliza un modelo simulado en los tests para poder comprobar la lógica del grafo sin utilizar una API Key.

## Traza

El archivo `traza_ejecucion.json` contiene un ejemplo de ejecución del agente.

La traza muestra las consultas realizadas a las herramientas, sus resultados y la respuesta final.

No se incluye el razonamiento interno del modelo.

## Estructura principal

```text
agente-langgraph/
├── README.md
├── main.py
├── agente.py
├── herramientas.py
├── datos_simulados.py
├── requirements.txt
├── .env.example
├── .gitignore
├── traza_ejecucion.json
└── tests/
```
