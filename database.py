import aiosqlite
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

async def get_conteo_usuario(user_id: int, generacion: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await _get_o_crear(db, user_id, generacion)
        return dict(row)

async def puede_registrar(user_id: int, tipo: str, generacion: int, limite) -> dict:
    conteo = await get_conteo_usuario(user_id, generacion)
    campo  = f"{tipo}_usados"
    usados = conteo.get(campo, 0)
    extras = conteo.get("slots_extra_disponibles", 0)
    if limite is None:
        return {"puede": True, "razon": "", "tiene_slot_extra": False}
    if usados < limite:
        return {"puede": True, "razon": "", "tiene_slot_extra": False}
    if extras > 0:
        return {"puede": False, "razon": f"Llegaste al límite de {tipo} ({limite}).", "tiene_slot_extra": True}
    return {"puede": False, "razon": f"Llegaste al límite ({limite}) y no tienes slots adicionales.", "tiene_slot_extra": False}

async def agregar_slot_extra(user_id: int, generacion: int, cantidad: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        await _get_o_crear(db, user_id, generacion)
        await db.execute("UPDATE slots_usuarios SET slots_extra_disponibles = slots_extra_disponibles + ? WHERE user_id = ? AND generacion = ?", (cantidad, user_id, generacion))
        await db.commit()

async def usar_slot_extra(user_id: int, tipo: str, generacion: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await _get_o_crear(db, user_id, generacion)
        if row["slots_extra_disponibles"] <= 0:
            return False
        campo = f"{tipo}_usados"
        await db.execute(f"UPDATE slots_usuarios SET {campo} = {campo} + 1, slots_extra_disponibles = slots_extra_disponibles - 1, slots_extra_usados = slots_extra_usados + 1 WHERE user_id = ? AND generacion = ?", (user_id, generacion))
        await db.commit()
        return True

async def registrar_personaje(user_id: int, tipo: str, generacion: int):
    """Suma 1 al conteo del tipo. tipo = 'estudiantes', 'profesores' o 'trabajadores'."""
    campo = f"{tipo}_usados"
    async with aiosqlite.connect(DB_PATH) as db:
        await _get_o_crear(db, user_id, generacion)
        await db.execute(f"UPDATE slots_usuarios SET {campo} = {campo} + 1 WHERE user_id = ? AND generacion = ?", (user_id, generacion))
        await db.commit()

async def restar_personaje(user_id: int, tipo: str, generacion: int):
    """
    Resta 1 al conteo al eliminar un personaje. No baja de 0.
    tipo = 'estudiantes', 'profesores' o 'trabajadores'
    """
    campo = f"{tipo}_usados"
    async with aiosqlite.connect(DB_PATH) as db:
        await _get_o_crear(db, user_id, generacion)
        await db.execute(f"UPDATE slots_usuarios SET {campo} = MAX(0, {campo} - 1) WHERE user_id = ? AND generacion = ?", (user_id, generacion))
        await db.commit()

async def reset_usuario(user_id: int, generacion: int):
    """
    Resetea TODOS los contadores de un usuario a 0 para una generación.
    Se usa en reset total o reset de slots desde admin-data.
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
