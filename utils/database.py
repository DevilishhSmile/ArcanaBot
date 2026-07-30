import aiosqlite
import asyncio
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "isefora.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS slots_usuarios (
                user_id                 INTEGER NOT NULL,
                generacion              INTEGER NOT NULL,
                estudiantes_usados      INTEGER DEFAULT 0,
                trabajadores_usados     INTEGER DEFAULT 0,
                profesores_usados       INTEGER DEFAULT 0,
                slots_extra_disponibles INTEGER DEFAULT 0,
                slots_extra_usados      INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, generacion)
            )
        """)
        await db.commit()

async def _get_o_crear(db, user_id, generacion):
    await db.execute("INSERT OR IGNORE INTO slots_usuarios (user_id, generacion) VALUES (?, ?)", (user_id, generacion))
    await db.commit()
    cur = await db.execute("SELECT * FROM slots_usuarios WHERE user_id = ? AND generacion = ?", (user_id, generacion))
    return await cur.fetchone()

# ──────────────────────────────────────────────
# CONTEO REAL DESDE SHEETS
# Siempre refleja la realidad, sin depender de SQLite
# ──────────────────────────────────────────────

def _contar_desde_sheets(user_id: int) -> dict:
    """
    Cuenta los personajes reales de un usuario directamente desde Sheets.
    Siempre obtiene datos frescos para evitar caché desactualizado.
    """
    from utils.sheets import get_sheet
    conteo = {"estudiantes": 0, "profesores": 0, "trabajadores": 0}
    try:
        for r in get_sheet("EstudiantesAprobados").get_all_records():
            if str(r.get("user_id","")) == str(user_id):
                conteo["estudiantes"] += 1
    except Exception as e:
        print(f"[DB] Error contando estudiantes: {e}")
    try:
        for r in get_sheet("Profesores").get_all_records():
            estado = str(r.get("estado","")).strip().upper()
            if str(r.get("user_id","")) == str(user_id) and                estado in ("APROBADO", ""):
                conteo["profesores"] += 1
    except Exception as e:
        print(f"[DB] Error contando profesores: {e}")
    try:
        for r in get_sheet("Trabajadores").get_all_records():
            estado = str(r.get("estado","")).strip().upper()
            if str(r.get("user_id","")) == str(user_id) and                estado in ("APROBADO", ""):
                conteo["trabajadores"] += 1
    except Exception as e:
        print(f"[DB] Error contando trabajadores: {e}")
    return conteo

async def _contar_desde_sheets_async(user_id: int) -> dict:
    """Versión async de _contar_desde_sheets para no bloquear el event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _contar_desde_sheets, user_id)

async def get_conteo_usuario(user_id: int, generacion: int) -> dict:
    """
    Retorna el conteo completo del usuario.
    Los personajes usados vienen de Sheets (fuente de verdad).
    Los slots extra vienen de SQLite.
    """
    # Slots extra desde SQLite
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await _get_o_crear(db, user_id, generacion)
        sqlite_data = dict(row)

    # Conteo real desde Sheets
    sheets_conteo = await _contar_desde_sheets_async(user_id)

    return {
        "user_id":               user_id,
        "generacion":            generacion,
        "estudiantes_usados":    sheets_conteo["estudiantes"],
        "profesores_usados":     sheets_conteo["profesores"],
        "trabajadores_usados":   sheets_conteo["trabajadores"],
        "slots_extra_disponibles": sqlite_data.get("slots_extra_disponibles", 0),
        "slots_extra_usados":      sqlite_data.get("slots_extra_usados", 0),
    }

async def puede_registrar(user_id: int, tipo: str, generacion: int, limite) -> dict:
    """
    Verifica si el usuario puede registrar un personaje del tipo dado.
    Cuenta desde Sheets para garantizar precisión.
    """
    if limite is None:
        return {"puede": True, "razon": "", "tiene_slot_extra": False}

    # Contar desde Sheets directamente
    sheets_conteo = await _contar_desde_sheets_async(user_id)
    tipo_key = tipo.rstrip("s")  # 'estudiantes' → 'estudiante', etc.
    usados   = sheets_conteo.get(tipo, 0)  # tipo ya viene como 'estudiantes'

    # Slots extra desde SQLite
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await _get_o_crear(db, user_id, generacion)
        extras = dict(row).get("slots_extra_disponibles", 0)

    if usados < limite:
        return {"puede": True, "razon": "", "tiene_slot_extra": False}
    if extras > 0:
        return {"puede": False,
                "razon": f"Llegaste al límite de {tipo} ({limite}).",
                "tiene_slot_extra": True}
    return {"puede": False,
            "razon": f"Llegaste al límite ({limite}) y no tienes slots adicionales.",
            "tiene_slot_extra": False}

async def agregar_slot_extra(user_id: int, generacion: int, cantidad: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        await _get_o_crear(db, user_id, generacion)
        await db.execute(
            "UPDATE slots_usuarios SET slots_extra_disponibles = slots_extra_disponibles + ? "
            "WHERE user_id = ? AND generacion = ?",
            (cantidad, user_id, generacion))
        await db.commit()

async def usar_slot_extra(user_id: int, tipo: str, generacion: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await _get_o_crear(db, user_id, generacion)
        if row["slots_extra_disponibles"] <= 0:
            return False
        campo = f"{tipo}_usados"
        await db.execute(
            f"UPDATE slots_usuarios SET {campo} = {campo} + 1, "
            f"slots_extra_disponibles = slots_extra_disponibles - 1, "
            f"slots_extra_usados = slots_extra_usados + 1 "
            f"WHERE user_id = ? AND generacion = ?",
            (user_id, generacion))
        await db.commit()
        return True

async def registrar_personaje(user_id: int, tipo: str, generacion: int):
    """
    Ya no necesita sumar en SQLite porque el conteo viene de Sheets.
    Se mantiene por compatibilidad con el código existente.
    """
    # El conteo real viene de Sheets — esta función ya no necesita hacer nada
    # pero la dejamos para no romper las llamadas existentes
    pass

async def restar_personaje(user_id: int, tipo: str, generacion: int):
    """
    Ya no necesita restar en SQLite porque el conteo viene de Sheets.
    Se mantiene por compatibilidad.
    """
    pass

async def reset_usuario(user_id: int, generacion: int):
    """
    Resetea solo los slots extra en SQLite.
    El conteo de personajes ya viene de Sheets.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE slots_usuarios SET
                estudiantes_usados      = 0,
                trabajadores_usados     = 0,
                profesores_usados       = 0,
                slots_extra_disponibles = 0,
                slots_extra_usados      = 0
            WHERE user_id = ? AND generacion = ?
        """, (user_id, generacion))
        await db.commit()
