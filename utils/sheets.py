import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(_BASE_DIR, "data", "credentials.json")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_client      = None
_spreadsheet = None

def _get_spreadsheet():
    global _client, _spreadsheet
    if _spreadsheet is None:
        from utils.constants import GOOGLE_SHEETS_ID
        if not os.path.exists(CREDENTIALS_PATH):
            raise FileNotFoundError(f"credentials.json no encontrado en: {CREDENTIALS_PATH}")
        creds        = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
        _client      = gspread.authorize(creds)
        _spreadsheet = _client.open_by_key(GOOGLE_SHEETS_ID)
        print("[SHEETS] ✅ Conectado a Google Sheets")
    return _spreadsheet

def get_sheet(sheet_name: str):
    return _get_spreadsheet().worksheet(sheet_name)

def get_all_rows(sheet_name: str) -> list:
    return get_sheet(sheet_name).get_all_records()

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ──────────────────────────────────────────────
# GLOBAL STATS
# ──────────────────────────────────────────────

def actualizar_global_stats():
    try:
        sheet = get_sheet("GlobalStats")
        rows  = sheet.get_all_values()

        def _aprobados(hoja):
            try: return sum(1 for r in get_all_rows(hoja) if r.get("estado","").upper() == "APROBADO")
            except Exception: return 0

        def _pendientes(hoja):
            try: return sum(1 for r in get_all_rows(hoja) if r.get("estado","").upper() == "PENDIENTE")
            except Exception: return 0

        def _total(hoja):
            try: return len(get_all_rows(hoja))
            except Exception: return 0

        stats = {
            "estudiantes_total":    _total("EstudiantesAprobados"),
            "trabajadores_total":   _aprobados("Trabajadores"),
            "profesores_total":     _aprobados("Profesores"),
            "uniformes_aprobados":  _total("UniformesAprobados"),
            "fichas_aprobadas":     _total("EstudiantesAprobados"),
            "trabajos_aprobados":   _aprobados("Trabajadores") + _aprobados("Profesores"),
            "pendientes_totales":   (_pendientes("UniformesPendientes") +
                                     _pendientes("EstudiantesPendientes") +
                                     _pendientes("TrabajosPendientes")),
            "uniformes_pendientes": _pendientes("UniformesPendientes"),
            "fichas_pendientes":    _pendientes("EstudiantesPendientes"),
            "trabajos_pendientes":  _pendientes("TrabajosPendientes"),
        }

        for i, row in enumerate(rows):
            if not row or len(row) < 1: continue
            cat = row[0].strip()
            if cat in stats:
                sheet.update_cell(i + 1, 2, stats[cat])

    except Exception as e:
        print(f"[SHEETS] Error actualizando GlobalStats: {e}")

def get_global_stats() -> dict:
    try:
        result = {}
        for row in get_sheet("GlobalStats").get_all_values():
            if len(row) >= 2 and row[0] not in ("categoria", ""):
                try: result[row[0].strip()] = int(row[1]) if row[1] else 0
                except (ValueError, TypeError): result[row[0].strip()] = 0
        return result
    except Exception as e:
        print(f"[SHEETS] Error leyendo GlobalStats: {e}")
        return {}

def get_uniformes_pendientes() -> list:
    try:
        return [r for r in get_all_rows("UniformesPendientes")
                if r.get("estado","").upper() == "PENDIENTE"]
    except Exception: return []

def get_fichas_pendientes() -> list:
    try:
        est  = [dict(r, _tipo="estudiante") for r in get_all_rows("EstudiantesPendientes")
                if r.get("estado","").upper() == "PENDIENTE"]
        trab = [dict(r, _tipo="trabajo") for r in get_all_rows("TrabajosPendientes")
                if r.get("estado","").upper() == "PENDIENTE"]
        return est + trab
    except Exception: return []

# ──────────────────────────────────────────────
# UNIFORMES
# ──────────────────────────────────────────────

def guardar_uniforme_pendiente(user_id, username, personaje, imagen, mensaje_id=0):
    get_sheet("UniformesPendientes").append_row([
        str(user_id), username, personaje, imagen,
        _now(), "PENDIENTE", "", "", "", str(mensaje_id)
    ], value_input_option="USER_ENTERED")

def aprobar_uniforme(user_id, personaje, imagen, staff_username):
    get_sheet("UniformesAprobados").append_row([
        str(user_id), personaje, imagen, _now(), staff_username, "APROBADO"
    ], value_input_option="USER_ENTERED")
    _actualizar_estado("UniformesPendientes", user_id, personaje, estado="APROBADO", staff=staff_username)
    actualizar_global_stats()

def rechazar_uniforme(user_id, personaje, staff_username, motivo):
    _actualizar_estado("UniformesPendientes", user_id, personaje, estado="RECHAZADO", staff=staff_username, motivo=motivo)
    actualizar_global_stats()

def has_approved_uniform(user_id, character_name) -> bool:
    try:
        for row in get_all_rows("UniformesAprobados"):
            if (str(row.get("user_id","")) == str(user_id) and
                    row.get("personaje","").strip().lower() == character_name.strip().lower()):
                return True
        return False
    except Exception as e:
        print(f"[SHEETS] Error verificando uniforme: {e}")
        return False

# ──────────────────────────────────────────────
# ESTUDIANTES
# ── FIX: aprobar_estudiante ahora guarda especie y casa ──
# ──────────────────────────────────────────────

def guardar_estudiante_pendiente(data, generacion, mensaje_id=0):
    get_sheet("EstudiantesPendientes").append_row([
        str(data["user_id"]), data["username"], data["personaje"],
        data.get("club",""), data.get("elemento",""), data.get("imagen",""),
        _now(), "", "", "", "PENDIENTE", "", "", str(generacion), str(mensaje_id),
    ], value_input_option="USER_ENTERED")

def aprobar_estudiante(data, generacion, staff_username, link_ficha=""):
    """
    Guarda el estudiante aprobado en EstudiantesAprobados.
    Columnas: user_id | username | personaje | elemento | club |
              link_ficha | fecha | staff_que_reviso | generacion | especie | casa
    Las columnas especie y casa deben existir en la hoja (añadirlas manualmente si no están).
    """
    get_sheet("EstudiantesAprobados").append_row([
        str(data["user_id"]),
        data["username"],
        data["personaje"],
        data.get("elemento", ""),
        # club: puede ser lista o string
        ", ".join(data.get("clubes_nombres", [])) if isinstance(data.get("clubes_nombres"), list)
            else data.get("club", ""),
        link_ficha,
        _now(),
        staff_username,
        str(generacion),
        data.get("especie", ""),   # columna especie — añadir a la hoja
        data.get("casa", ""),      # columna casa    — añadir a la hoja
    ], value_input_option="USER_ENTERED")
    _actualizar_estado("EstudiantesPendientes", data["user_id"], data["personaje"],
                       estado="APROBADO", staff=staff_username)
    actualizar_global_stats()

def rechazar_estudiante(data, staff_username, motivo):
    _actualizar_estado("EstudiantesPendientes", data["user_id"], data["personaje"],
                       estado="RECHAZADO", staff=staff_username, motivo=motivo)
    actualizar_global_stats()

# ──────────────────────────────────────────────
# TRABAJOS
# ── FIX: aprobar_profesor/trabajador ahora guarda casa ──
# ──────────────────────────────────────────────

def guardar_trabajo_pendiente(data, tipo, mensaje_id=0):
    cargo   = data.get("clase","") if tipo == "profesor" else data.get("cargo","")
    materia = data.get("clase","") if tipo == "profesor" else ""
    get_sheet("TrabajosPendientes").append_row([
        str(data["user_id"]), data["username"], data["personaje"],
        cargo, "", materia, "", _now(),
        "PENDIENTE", "", "", "", "", str(mensaje_id),
    ], value_input_option="USER_ENTERED")

def aprobar_profesor(data, generacion, staff_username, link_ficha=""):
    """
    Columnas: user_id | username | personaje | materia | subcargo (si aplica) |
              link_ficha | fecha | staff_que_reviso | estado | generacion
    """
    get_sheet("Profesores").append_row([
        str(data["user_id"]),
        data["username"],
        data["personaje"],
        data.get("clase", ""),
        data.get("subcargo", ""),
        link_ficha,
        _now(),
        staff_username,
        "APROBADO",
        str(generacion),
    ], value_input_option="USER_ENTERED")
    _actualizar_estado_trabajos(data["user_id"], data["personaje"], estado="APROBADO", staff=staff_username)
    actualizar_global_stats()

def aprobar_trabajador(data, generacion, staff_username, link_ficha=""):
    """
    Columnas: user_id | username | personaje | cargo | subcargo (si aplica) |
              link_ficha | fecha | staff_que_reviso | estado | generacion
    """
    get_sheet("Trabajadores").append_row([
        str(data["user_id"]),
        data["username"],
        data["personaje"],
        data.get("cargo", ""),
        data.get("subcargo", ""),
        link_ficha,
        _now(),
        staff_username,
        "APROBADO",
        str(generacion),
    ], value_input_option="USER_ENTERED")
    _actualizar_estado_trabajos(data["user_id"], data["personaje"], estado="APROBADO", staff=staff_username)
    actualizar_global_stats()

def rechazar_trabajo(data, staff_username, motivo):
    _actualizar_estado_trabajos(data["user_id"], data["personaje"],
                                estado="RECHAZADO", staff=staff_username, motivo=motivo)
    actualizar_global_stats()

def eliminar_personaje_sheets(user_id: int, personaje: str, tipo: str) -> bool:
    hoja_map = {
        "estudiante": "EstudiantesAprobados",
        "profesor":   "Profesores",
        "trabajador": "Trabajadores",
    }
    hoja = hoja_map.get(tipo)
    if not hoja: return False
    try:
        sheet = get_sheet(hoja)
        rows  = sheet.get_all_values()
        for i, row in enumerate(rows):
            if i == 0: continue
            if len(row) >= 3 and str(row[0]) == str(user_id) and \
               row[2].strip().lower() == personaje.strip().lower():
                sheet.delete_rows(i + 1)
                actualizar_global_stats()
                return True
        return False
    except Exception as e:
        print(f"[SHEETS] Error eliminando personaje: {e}")
        return False

def get_personajes_usuario(user_id: int) -> list:
    """
    Devuelve todos los personajes aprobados de un usuario.
    FIX: ahora incluye especie, elemento, casa para el sistema de IDs.
    """
    personajes = []
    try:
        for r in get_all_rows("EstudiantesAprobados"):
            if str(r.get("user_id","")) == str(user_id):
                personajes.append({
                    "tipo":      "estudiante",
                    "personaje": r.get("personaje", ""),
                    "detalle":   r.get("elemento", ""),
                    # Datos completos para el ID
                    "elemento":  r.get("elemento", ""),
                    "especie":   r.get("especie", ""),
                    "casa":      r.get("casa", ""),
                    "fecha_aprobacion": r.get("fecha", ""),
                })
    except Exception: pass
    try:
        for r in get_all_rows("Profesores"):
            if str(r.get("user_id","")) == str(user_id) and r.get("estado","").upper() == "APROBADO":
                personajes.append({
                    "tipo":      "profesor",
                    "personaje": r.get("personaje", ""),
                    "detalle":   r.get("materia", ""),
                    # Datos completos para el ID
                    "materia":   r.get("materia", ""),
                    "subcargo":  r.get("subcargo (si aplica)", ""),
                    "fecha_aprobacion": r.get("fecha", ""),
                })
    except Exception: pass
    try:
        for r in get_all_rows("Trabajadores"):
            if str(r.get("user_id","")) == str(user_id) and r.get("estado","").upper() == "APROBADO":
                personajes.append({
                    "tipo":      "trabajador",
                    "personaje": r.get("personaje", ""),
                    "detalle":   r.get("cargo", ""),
                    # Datos completos para el ID
                    "cargo":     r.get("cargo", ""),
                    "subcargo":  r.get("subcargo (si aplica)", ""),
                    "fecha_aprobacion": r.get("fecha", ""),
                })
    except Exception: pass
    return personajes

def get_profesores_aprobados_por_materia(materia) -> int:
    try:
        return sum(1 for r in get_all_rows("Profesores")
                   if r.get("materia","").strip() == materia and r.get("estado","").upper() == "APROBADO")
    except Exception: return 0

def get_trabajadores_aprobados_por_cargo(cargo) -> int:
    try:
        return sum(1 for r in get_all_rows("Trabajadores")
                   if r.get("cargo","").strip() == cargo and r.get("estado","").upper() == "APROBADO")
    except Exception: return 0

# ── HELPERS INTERNOS ──────────────────────────

def _actualizar_estado(sheet_name, user_id, personaje, estado="", staff="", motivo="", link_ficha=""):
    try:
        sheet   = get_sheet(sheet_name)
        rows    = sheet.get_all_values()
        if not rows: return
        headers = rows[0]
        col_map = {h: i+1 for i, h in enumerate(headers)}
        now     = _now()
        for i, row in enumerate(rows[1:], start=2):
            if len(row) > 2 and str(row[0]) == str(user_id) and \
               row[2].strip().lower() == personaje.strip().lower():
                if "estado" in col_map and estado:
                    sheet.update_cell(i, col_map["estado"], estado)
                if "staff_que_reviso" in col_map and staff:
                    sheet.update_cell(i, col_map["staff_que_reviso"], staff)
                if "fecha_resolucion" in col_map:
                    sheet.update_cell(i, col_map["fecha_resolucion"], now)
                if "motivo_rechazo" in col_map and motivo:
                    sheet.update_cell(i, col_map["motivo_rechazo"], motivo)
                if "link_ficha_final" in col_map and link_ficha:
                    sheet.update_cell(i, col_map["link_ficha_final"], link_ficha)
                break
    except Exception as e:
        print(f"[SHEETS] Error actualizando {sheet_name}: {e}")

def _actualizar_estado_trabajos(user_id, personaje, estado="", staff="", motivo=""):
    _actualizar_estado("TrabajosPendientes", user_id, personaje,
                       estado=estado, staff=staff, motivo=motivo)

# ── LEGACY ────────────────────────────────────
def append_row(sheet_name, row):
    get_sheet(sheet_name).append_row(row, value_input_option="USER_ENTERED")

def delete_row_by_value(sheet_name, column_index, value) -> bool:
    sheet = get_sheet(sheet_name)
    for i, row in enumerate(sheet.get_all_values()):
        if i == 0: continue
        if len(row) >= column_index and \
           str(row[column_index-1]).strip().lower() == str(value).strip().lower():
            sheet.delete_rows(i + 1)
            return True
    return False
