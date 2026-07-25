import os
from dotenv import load_dotenv

load_dotenv()

GENERACION_ACTUAL = 1

# =============================================
# SLOTS POR GENERACIÓN — EDITAR AQUÍ
# =============================================
SLOTS_CONFIG = {
    1: {"estudiantes": 3, "trabajadores": 2, "profesores": 2},
    "default": {"estudiantes": 3, "trabajadores": 2, "profesores": 2}
}

def get_slots_config():
    return SLOTS_CONFIG.get(GENERACION_ACTUAL, SLOTS_CONFIG["default"])

TOKEN            = os.getenv("DISCORD_TOKEN")
GUILD_ID         = int(os.getenv("GUILD_ID", 0))
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")

CANAL_ENVIAR_UNIFORME      = int(os.getenv("CANAL_ENVIAR_UNIFORME", 0))
CANAL_REGISTRAR_ESTUDIANTE = int(os.getenv("CANAL_REGISTRAR_ESTUDIANTE", 0))
CANAL_REGISTRO_TRABAJOS    = int(os.getenv("CANAL_REGISTRO_TRABAJOS", 0))
CANAL_CARTA_ACEPTACION     = int(os.getenv("CANAL_CARTA_ACEPTACION", 0))
CANAL_FICHAS_ESTUDIANTES   = int(os.getenv("CANAL_FICHAS_ESTUDIANTES", 0))
CANAL_FICHAS_PROFESORES    = int(os.getenv("CANAL_FICHAS_PROFESORES", 0))
CANAL_FICHAS_TRABAJADORES  = int(os.getenv("CANAL_FICHAS_TRABAJADORES", 0))
CANAL_REVISION_UNIFORMES   = int(os.getenv("CANAL_REVISION_UNIFORMES", 0))
CANAL_REVISION_FICHAS      = int(os.getenv("CANAL_REVISION_FICHAS", 0))
CANAL_LOGS_BOT             = int(os.getenv("CANAL_LOGS_BOT", 0))
CANAL_SANCIONES            = int(os.getenv("CANAL_SANCIONES", 0))  # Canal donde se notifican sanciones

ROL_STAFF          = int(os.getenv("ROL_STAFF", 0))
ROL_ESTUDIANTE     = int(os.getenv("ROL_ESTUDIANTE", 0))
ROL_PROFESOR       = int(os.getenv("ROL_PROFESOR", 0))
ROL_TRABAJADOR     = int(os.getenv("ROL_TRABAJADOR", 0))
ROL_SLOT_ADICIONAL = 1217564303612182610
ROL_REGISTRADO     = 1221480425042739363
ROL_CONSEJO        = 1187541476415119370  # Consejo Estudiantil — puede asignar PC

# Roles que pueden asignar PC y aplicar sanciones
# ── EDITAR AQUÍ si cambian los roles con autoridad ──
ROLES_AUTORIDAD_PC = [ROL_STAFF, ROL_PROFESOR, ROL_CONSEJO]

COLOR_PENDIENTE  = 0x9B59B6
COLOR_APROBADO   = 0x7B2FBE
COLOR_RECHAZADO  = 0x8E44AD
COLOR_INFO       = 0xA569BD
COLOR_ACEPTACION = 0x9B59B6

# =============================================
# CARGOS — EDITAR AQUÍ
# =============================================
CARGOS = {
    "Bibliotecario":              2,
    "Secretario":                 2,
    "Enfermero":                  3,
    "Consejero estudiantil":      3,
    "Inspector":                  None,
    "Psicólogo":                  None,
    "Conserje":                   None,
    "Prefecto":                   None,
    "Coordinador de eventos":     None,
    "Coordinador comportamental": None,
    "Encargado de cocina":        None,
    "Decano":                     1,
    "Guardia":                    None,
    "Trabajador general":         None,
}

# =============================================
# MATERIAS — EDITAR AQUÍ
# =============================================
MATERIAS = [
    "Criminología", "Química", "Astronomía", "Biología", "Debate",
    "Diplomacia", "Lenguaje mítico", "Economía imperial", "Mitología",
    "Literatura antigua", "Ciencias elementales", "Matemáticas místicas",
    "Historia de la magia", "Runas ancestrales", "Filosofía alquímica",
    "Geografía mágica", "Alquimia", "Botánica mágica", "Bestias mágicas",
    "Morfología", "Cocina", "Artes escénicas y creativas",
    "Defensa y entrenamiento físico", "Psicología mágica",
    "Estrategia y tácticas mágicas", "Profesor sustituto",
]

MATERIAS_LIMITE = {m: 1 for m in MATERIAS}
MATERIAS_LIMITE["Profesor sustituto"] = 3

# =============================================
# CLUBES — EDITAR AQUÍ
# =============================================
CLUBES = {
    "Danza":      1181462496096297020,
    "Porrismo":   1181462524500115517,
    "Deportes":   1181462560105578516,
    "Alquimia":   1181462708411973683,
    "Cocina":     1181463153876422676,
    "Natación":   1181463211401289748,
    "Actuación":  1181463424031522826,
    "Jardinería": 1484679116987830362,
    "Debate":     1490754426091081758,
    "Astronomía": 1484677853089103942,
    "Literatura": 1181463472215691375,
    "Música":     1490755565318570125,
    "Ballet":     1490755961089167481,
    "Fotografía": 1488980104552906752,
}

# =============================================
# SISTEMA PCA — Puntos de Canje Académico
# ── EDITAR AQUÍ si cambian las reglas ──
# =============================================

# Tabla de notas → PC
# Formato: (nota_minima, nota_maxima, pc_otorgados)
TABLA_NOTAS_PC = [
    (3.5, 3.5,  1),
    (3.6, 3.9,  3),
    (4.0, 4.4,  5),
    (4.5, 4.9,  7),
    (5.0, 5.0, 10),
]

# Trabajo sucio del Consejo: rango de PC permitido
PC_TRABAJO_SUCIO_MIN = 5
PC_TRABAJO_SUCIO_MAX = 10

# Tipos de sanción
TIPOS_SANCION = {
    "castigo_menor": {
        "nombre":        "Castigo Menor",
        "duracion_min":  5,    # minutos
        "duracion_max":  20,   # minutos
        "canjeable_pct": 0.75, # 75% canjeable
        "min_obligatorio": 5,  # minutos mínimos no canjeables
        "pc_por_minuto": 1/1.5,  # 1 PC = 1.5 min → 1 min = 0.67 PC
        "bonificacion_pc": 10,   # PC para activar bonificación
        "bonificacion_min": 1,   # minutos extra de reducción con bonificación
        "descripcion": "5-20 minutos de tiempo de rol",
    },
    "detencion": {
        "nombre":        "Detención",
        "duracion_min":  30,   # minutos
        "duracion_max":  120,  # minutos
        "canjeable_pct": 0.80, # 80% canjeable
        "min_obligatorio": None,  # calculado dinámicamente
        "pc_por_minuto": 1/2.5,   # 1 PC = 2.5 min → 1 min = 0.4 PC
        "bonificacion_pc": None,
        "bonificacion_min": None,
        "descripcion": "30-120 minutos de tiempo de rol",
    },
    "suspension": {
        "nombre":        "Suspensión",
        "duracion_min":  2,    # días IRL
        "duracion_max":  3,    # días IRL
        "canjeable_pct": None, # solo se puede quitar 1 día por 20 PC
        "min_obligatorio": 1,  # siempre queda al menos 1 día
        "pc_por_dia": 20,      # 20 PC = 1 día menos
        "descripcion": "2-3 días IRL (requiere autorización del staff)",
        "requiere_autorizacion": True,
    },
}

def calcular_pc_por_nota(nota: float) -> int:
    """Retorna los PC correspondientes a una nota académica."""
    if nota < 3.5:
        return 0
    for (min_n, max_n, pc) in TABLA_NOTAS_PC:
        if min_n <= nota <= max_n:
            return pc
    return 0

def calcular_reduccion_castigo_menor(pc_a_gastar: int, duracion: int = 20) -> dict:
    """
    Calcula la reducción para castigos menores.
    Retorna dict con minutos_reducidos, tiempo_final, bonificacion_aplicada.
    """
    max_canjeable = int(duracion * 0.75)
    min_obligatorio = duracion - max_canjeable  # normalmente 5 min

    # Máximo PC que tiene sentido gastar
    pc_max = 10  # para la reducción completa

    pc = min(pc_a_gastar, pc_max)
    minutos_reducidos = min(pc * 1.5, max_canjeable)
    bonificacion = False
    bonus_min = 0

    if pc_a_gastar >= 10:
        bonificacion = True
        bonus_min = 1
        minutos_reducidos += bonus_min

    tiempo_final = max(min_obligatorio - bonus_min, duracion - minutos_reducidos)
    return {
        "minutos_reducidos": minutos_reducidos,
        "tiempo_final":      tiempo_final,
        "bonificacion":      bonificacion,
        "min_obligatorio":   min_obligatorio,
    }

def calcular_reduccion_detencion(pc_a_gastar: int, duracion: int) -> dict:
    """
    Calcula la reducción para detención.
    1 PC = 2.5 minutos. Máximo canjeable: 80%.
    """
    max_canjeable   = int(duracion * 0.80)
    min_obligatorio = duracion - max_canjeable

    minutos_reducidos = min(pc_a_gastar * 2.5, max_canjeable)
    tiempo_final = max(min_obligatorio, duracion - minutos_reducidos)

    return {
        "minutos_reducidos": minutos_reducidos,
        "tiempo_final":      tiempo_final,
        "min_obligatorio":   min_obligatorio,
        "max_canjeable":     max_canjeable,
    }

def calcular_reduccion_suspension(pc_a_gastar: int, duracion_dias: int) -> dict:
    """
    20 PC = 1 día de reducción. Siempre queda al menos 1 día.
    """
    dias_reducibles = duracion_dias - 1  # siempre queda 1 día
    dias_a_reducir  = min(pc_a_gastar // 20, dias_reducibles)
    pc_usados       = dias_a_reducir * 20
    dias_final      = duracion_dias - dias_a_reducir

    return {
        "dias_reducidos": dias_a_reducir,
        "dias_final":     dias_final,
        "pc_usados":      pc_usados,
        "pc_sobrante":    pc_a_gastar - pc_usados,
    }
