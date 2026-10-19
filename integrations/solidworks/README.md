# SolidWorks MCP - integración

Servidor: [SolidworksMCP-python](https://github.com/andrewbartels1/SolidworksMCP-python) (134 tools, FastMCP, MIT).
Versión fijada: `fdfe016` (ver `run-mock.sh`).

## Qué se puede y qué no (verificado)

SolidWorks se controla por **COM de Windows** (pywin32, hilo STA). Una sesión en la nube/Linux **no puede** hablar con SolidWorks directamente; el propio proyecto lo dice y lo comprobé: el adaptador real solo existe en Windows.

| Entorno | Qué funciona |
|---|---|
| Sesión cloud / Linux (aquí) | Servidor en **modo mock**: valida la secuencia de llamadas y los esquemas. Resultados simulados (la masa/volumen no son reales; `create_cut_extrude` ni existe en el mock). |
| Windows con SolidWorks | **Modo real** con Claude Code local (stdio). Es el camino recomendado. |
| Cloud/Linux -> Windows | Puente HTTP (más abajo). Requiere túnel y es tu decisión de seguridad. |

## Qué hay en el repo

| Archivo | Para qué |
|---|---|
| `.mcp.json` | Registra `solidworks-mock` (proyecto). **Claude Code pide aprobarlo una vez** (`claude` -> `/mcp`). |
| `integrations/solidworks/run-mock.sh` | Primera ejecución: baja el commit fijado a `.vendor/` (ignorado por git), crea venv e instala (~11 s). Después solo arranca. |
| `integrations/solidworks/mcp.windows.example.json` | Config para tu PC Windows con `--real`. |
| `integrations/solidworks/http_bridge.py` | Servidor HTTP con token Bearer (ver abajo). |
| `integrations/solidworks/sw.py` | Ejecuta una lista JSON de llamadas en una sola sesión y se detiene al primer error. Sirve contra mock o contra el puente. |
| `integrations/solidworks/examples/` | Ejemplo `mounting_plate.json`. |
| `.claude/skills/solidworks-mcp/SKILL.md` | Manual operativo: convenciones, flujo, verificación, trampas de COM. |

## Uso rápido

```bash
# listar tools / ejecutar un guion en mock
.vendor/SolidworksMCP-python/.venv/bin/python -I integrations/solidworks/sw.py --list
.vendor/SolidworksMCP-python/.venv/bin/python -I integrations/solidworks/sw.py integrations/solidworks/examples/mounting_plate.json
```

## Modo real en Windows (recomendado)

1. Clona SolidworksMCP-python, Python 3.13 de python.org, `python -m venv .venv`, `.venv\Scripts\python.exe -m pip install -e .`
2. **Abre SolidWorks primero.**
3. Copia `mcp.windows.example.json` a tu `.mcp.json` (ajusta rutas y año). `--real` es obligatorio: sin él corre en mock sin avisar.
4. Reinicia Claude Code, `/mcp` debe mostrar `solidworks` conectado y el log `Connected to SolidWorks`.

## Puente HTTP (cloud/Linux -> Windows)

El modo remoto documentado por el proyecto (`--mode remote`) **falla al arrancar** (`Already running asyncio in this thread`: llama a `FastMCP.run()` síncrono dentro de un loop activo). Además su modo HTTP no autentica en el transporte, y el servidor puede abrir/sobrescribir archivos y ejecutar VBA. Por eso `http_bridge.py` arranca con `run_http_async` y rechaza (401) toda petición sin `Authorization: Bearer <token>`.
Probado en mock: sin token 401, token erróneo 401, token correcto lista 134 tools y ejecuta `create_part`. **No probado contra SolidWorks real** (no hay Windows aquí).

```powershell
$env:SOLIDWORKS_MCP_BRIDGE_TOKEN = "<secreto largo>"
.venv\Scripts\python.exe integrations\solidworks\http_bridge.py --real --year 2026 --port 8765   # escucha en 127.0.0.1
```

Alcánzalo con un túnel privado (SSH `-L`, Tailscale, etc.); no lo expongas a Internet. Si el túnel cambia el header `Host`, usa `--allowed-host`. Además la red de la sesión cloud debe permitir ese destino (ver la configuración de red del entorno).

## Limitaciones conocidas

- Mock != SolidWorks. Cualquier cifra del mock hay que ignorarla.
- Todo lo marcado como "real" en el SKILL viene de la documentación upstream (pruebas en SW 2025/2026 del autor); aquí no se pudo reproducir.
- Proyecto "hobby/research" en construcción según su README; versión fijada para evitar cambios inesperados.
