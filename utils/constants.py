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

ROL_STAFF          = int(os.getenv("ROL_STAFF", 0))
ROL_ESTUDIANTE     = int(os.getenv("ROL_ESTUDIANTE", 0))
ROL_PROFESOR       = int(os.getenv("ROL_PROFESOR", 0))
ROL_TRABAJADOR     = int(os.getenv("ROL_TRABAJADOR", 0))
ROL_SLOT_ADICIONAL = 1217564303612182610  # +Slot de Personaje

SHEET_UNIFORMES_PENDIENTES   = "UniformesPendientes"
SHEET_UNIFORMES_APROBADOS    = "UniformesAprobados"
SHEET_ESTUDIANTES_PENDIENTES = "EstudiantesPendientes"
SHEET_ESTUDIANTES_APROBADOS  = "EstudiantesAprobados"
SHEET_PROFESORES             = "Profesores"
SHEET_TRABAJADORES           = "Trabajadores"

COLOR_PENDIENTE  = 0x9B59B6
COLOR_APROBADO   = 0x7B2FBE
COLOR_RECHAZADO  = 0x8E44AD
COLOR_INFO       = 0xA569BD
COLOR_ACEPTACION = 0x9B59B6  # Morado para carta de aceptación

# =============================================
# CARGOS — EDITAR AQUÍ
# None = 1 cupo único / int = cantidad de cupos
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
# 1 cupo por materia / "Profesor sustituto" = 3
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
# Formato: "Nombre": ID_del_rol_en_Discord
# Sin límite de miembros / multi-selección permitida
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
