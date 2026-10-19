---
name: solidworks-mcp
description: Operate SolidWorks through the SolidworksMCP-python MCP server (134 tools - parts, sketches, assemblies, drawings, export, VBA). Use when asked to model, inspect, modify or export CAD in SolidWorks, or to plan a CAD project that will be built with that server. Covers mock vs real mode, call conventions, build workflow, verification and the COM pitfalls that cause silent failures.
---

# SolidWorks MCP - operating manual

Server: https://github.com/andrewbartels1/SolidworksMCP-python (pinned in `integrations/solidworks/run-mock.sh`).
Integration notes and setup: `integrations/solidworks/README.md`.

## 0. First thing: which mode am I in?

| Server name | Mode | What it means |
|---|---|---|
| `solidworks-mock` (this repo's `.mcp.json`, Linux/cloud) | MOCK | Simulated. Nothing touches SolidWorks. Use to validate a plan/call sequence only. |
| `solidworks` (Windows machine, `--real`) | REAL | COM automation of a running SolidWorks. Windows only. |

Real COM needs Windows + SolidWorks (STA COM via pywin32). A Linux container can never drive it directly.
**Mock output is not engineering truth**: in testing, a 120x80x8 mm plate reported 93 029 mm^3 (true: 76 800). Never quote mock mass/volume/size as results. Mock also lacks some tools (`create_cut_extrude` -> "not implemented by this adapter"). A mock pass proves the call *shape* is valid, not that SolidWorks will accept it.
If a tool result looks like blank images / nonsense numbers in a session that should be real, `--real` is probably missing.

If no `mcp__solidworks*` tools are attached (project servers need one-time approval via `claude` -> `/mcp`), run the same calls with `integrations/solidworks/sw.py steps.json`.

## 1. Call conventions (verified)

- Almost every tool takes ONE argument object: `{"input_data": {...fields...}}`. Tools with no arguments take none: `exit_sketch`, `get_model_info`, `list_components`, `list_configurations`, `list_open_documents`, `get_material_properties`, `get_file_properties`, `get_selected_entities`.
- `list_features` needs `input_data` even though every field is optional: pass `{"input_data": {}}`.
- Units in the tool API are **millimetres** (degrees for angles). Exception: coordinate hints in `add_fillet/add_chamfer.edge_names` (`"x,y,z"`) are in **metres**.
- Every result has `status` ("success"/"error"), `message`, `execution_time` plus a payload. **Always check `status`; stop on the first error** - tool failures come back as `status: "error"` (only schema-validation mistakes raise a protocol error).
- Plane names for `create_sketch.plane`: `Front`, `Top`, `Right` (case-sensitive; also XY/XZ/YZ). Other tools want the tree name: `Front Plane`, `Right Plane`. Localised SolidWorks installs name planes differently (e.g. "Planta").
- Names are generated: sketches `Sketch1, Sketch2...`, features `Boss-Extrude1`, `Fillet1`... Read them back from the result; pass `sketch_name` explicitly to `create_extrusion` / `create_cut_extrude` instead of relying on "most recent".
- File paths: absolute, short, ASCII. One active document per task.

## 2. Standard build loop

1. **Inspect**: `list_open_documents`, `get_model_info`, `list_features(include_suppressed=true)`, `get_mass_properties`. For an existing part also `classify_feature_tree` - do not rebuild from a silhouette.
2. **Plan** the call list in text, with dimensions and units; get approval before irreversible steps.
3. **Execute in checkpoints** of one intent each ("base profile", "holes", "fillets"). Order: `create_part` -> `create_sketch` -> geometry (`add_rectangle/add_circle/add_line/add_arc/add_centerline`) -> `exit_sketch` -> feature (`create_extrusion` / `create_revolve` / `create_cut_extrude` / `create_sweep` / `create_loft`) -> `add_fillet/add_chamfer` -> `save_as`.
4. **Verify with geometry, not with feature count** (see 4). Compare `get_mass_properties` volume to the volume you computed by hand.
5. Export: `export_step` / `export_stl` / `export_pdf` / `export_image`; assemblies: `create_assembly`, `insert_component` (file must contain a solid body), `list_components`, `add_mate` (only planes/axes by tree name).

Tool families: modeling (`create_*`, `add_fillet`, `mirror_feature`, `pattern_circular`, `create_reference_plane/axis`), sketching (`add_*`, `sketch_*`, constraints/dimensions), drawing (`create_drawing_view`, `add_dimension`, `create_section_view`, ...), analysis (`get_mass_properties`, `check_interference`), export, file mgmt, templates, macros, VBA generation (`generate_vba_*`), API-doc lookup (`search_solidworks_api_help`, `lookup_api_method`).
Revolve needs a `add_centerline` axis in the sketch; `create_revolve(axis_entity="Centerline1")`.
For loft/sweep/sheet-metal/surfacing beyond direct tool support, route to `generate_vba_part_modeling` and say so in the plan.

## 3. Prompt contract for reliable runs

Goal (one sentence) / Inputs (units, every dimension, absolute save path) / Constraints (plane, stop on first failure, never invent values) / Verification (per-call tool+status, final dimensions, output paths). Ask the user for missing dimensions instead of guessing.
Do not click in SolidWorks while a chain runs; one human edit between calls can change the selection or active document.

## 4. Silent-failure traps (from upstream `docs/agents/com-api-pitfalls.md`, real-mode)

- Success / "feature appeared in tree" != geometry changed. `FeatureChamferType` and a mis-resolved edge both "succeed" with the wrong or zero effect. Verify volume delta against an expected value.
- Edge selection by coordinate can silently pick a neighbour edge at shared boundaries (hole rim flush with a face): use `edge_names=["face:x,y,z"]` (whole face) or leave `edge_names` empty to act on the user's live selection (`get_selected_entities` first).
- `get_mass_properties` (and anything that forces a rebuild) **clears the live selection**: measure *before* reading/using a selection.
- `ThroughAll` from a mid-plane sketch cuts one direction only; use `ThroughAllBoth` / `both_directions`.
- `insert_component` / `add_mate` can return "success" while nothing moved; confirm with `list_components` and a before/after check.
- Never hand-roll `ToolsCheckInterference2` in VBA/COM: under late binding it reports 0 interferences always. Use the `check_interference` tool (upstream uses the interference-detection manager).
- Default templates: part/assembly/drawing template slots are 8/9/10 on SW2025; empty template path breaks `create_*`.
- `export_image` captures the frontmost window; activate the target doc first (`activate_document`).
- `execute_macro` needs a binary `.swp` authored in SolidWorks; a text-generated one pops a modal dialog that hangs the COM thread. `generate_vba_*` produces source only.
- Heavy documents (>~1 MB parts) can crash SLDWORKS during batch export: throttle (~10 s between parts), do heavy files last, and abort the batch if `get_model_info` returns type "Unknown".
- Circuit breaker: after repeated failures tools fail fast ("Circuit breaker is open") for ~30-60 s.

## 5. Troubleshooting (real mode)

1. "No active model" + OpenDoc6 errors together -> stale COM handle after SolidWorks restarted: restart the MCP server (restarting the client, not just SolidWorks).
2. "Member not found" / NoneType not callable after a SolidWorks upgrade -> delete `%TEMP%\gen_py`, restart server.
3. Everything fails with `RPC server is unavailable` -> SLDWORKS.exe died; restart both.
4. Host reports `invalid_union` / JSON parse errors -> config points at `start_local_server.py` (banner on stdout); must be `start_local_server_claude.py`.
5. Files in a PDM vault fail to open unless checked out; SW2025 SP0 can crash opening drawings.

## 6. Reusing work

Replayable scripts: `integrations/solidworks/sw.py steps.json` (guarded, stops on first error). Upstream "SolidWorks as Code": set `SOLIDWORKS_MCP_SOC_LOGGING_ENABLED=true` on the server to log every call to SQLite and export a runnable script with `python -m solidworks_mcp.agents.soc_exporter <session> out.py` (real adapter only).
Reference builds: upstream `docs/getting-started/tutorial-parts/build_u_bracket_artifact.py`, yoke/U-joint tutorials.
