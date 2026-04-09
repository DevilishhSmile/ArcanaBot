import re
import discord
from utils.constants import COLOR_PENDIENTE, COLOR_APROBADO, COLOR_INFO, COLOR_ACEPTACION

def remove_emojis(text: str) -> str:
    emoji_pattern = re.compile(
        "[" "\U0001F600-\U0001F64F" "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF" "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0" "\U000024C2-\U0001F251" "]+", flags=re.UNICODE)
    return emoji_pattern.sub("", text).strip()

def is_valid_character_name(name: str) -> bool:
    name = name.strip()
    if len(name) < 2 or len(name) > 50: return False
    if re.search(r"\d", name): return False
    if not re.match(r"^[\w\sÁáÉéÍíÓóÚúÜüÑñ\-']+$", name): return False
    return True

def default_if_empty(value: str, default: str = "No especificado") -> str:
    return value.strip() if value and value.strip() else default

def clean_field(text: str) -> str:
    return re.sub(r"\s+", " ", remove_emojis(text)).strip()

def validar_edad_estudiante(edad_str: str) -> tuple[bool, str]:
    """Valida que la edad del estudiante sea un número entre 1 y 18."""
    try:
        edad = int(edad_str.strip())
        if edad > 18:
            return False, f"❌ Los estudiantes tienen edad **máxima de 18 años**. Ingresaste **{edad}**."
        if edad < 1:
            return False, "❌ La edad debe ser mayor a 0."
        return True, ""
    except ValueError:
        return False, "❌ La edad debe ser un número."

def validar_edad_adulto(edad_str: str) -> tuple[bool, str]:
    """Valida que la edad de profesores/trabajadores sea mínimo 25."""
    try:
        edad = int(edad_str.strip())
        if edad < 25:
            return False, f"❌ Profesores y trabajadores tienen edad **mínima de 25 años**. Ingresaste **{edad}**."
        return True, ""
    except ValueError:
        return False, "❌ La edad debe ser un número."

# ──────────────────────────────────────────────
# FORMATOS DE FICHA RP — Nuevos formatos estéticos
# ──────────────────────────────────────────────

def format_student_sheet(data: dict) -> str:
    clubes = data.get("clubes_nombres", data.get("club", "No especificado"))
    if isinstance(clubes, list):
        clubes = ", ".join(clubes) if clubes else "Ninguno"

    hobbies   = data.get("hobbies",   "No especificado")
    gustos    = data.get("gustos",    "No especificado")
    disgustos = data.get("disgustos", "No especificado")

    return (
        "╭─────┈╯  𓈃  ⋆ ࣪.  🔮 ◌Ⳋ𝅄\n"
        " `💌`     ࣪  *𝑫𝒆𝒂𝒓* ࣪  ᚐ  ִ  *𝑺𝒕𝒖𝒅𝒆𝒏𝒕* ބ  ࣪\n"
        f"⊹ ࣪ ˖           __{data['personaje']}__ ✶  __{data['edad']}__ ˚. ᵎᵎ\n"
        f"⊹ ࣪ ˖           __{data['especie']}__ ✶  __{data['pronouns']}__ ˚. ᵎᵎ\n"
        f"⊹ ࣪ ˖           __{data['elemento']}__ ✶ __{clubes}__ ˚. ᵎᵎ\n"
        "︶⊹︶︶⠀𖥔  ︶︶⊹︶\n"
        f"⊹ ࣪ ˖  **Poderes/Habilidades;** {data['habilidades']}\n"
        f"⊹ ࣪ ˖  **Debilidades;** {data['debilidades']}\n"
        "︶⊹︶︶⠀𖥔  ︶︶⊹︶\n"
        f"⊹ ࣪ ˖  **Personalidad;** {data['personalidad']}\n"
        f"⊹ ࣪ ˖  **Historia;** {data['historia']}\n"
        "︶⊹︶︶⠀𖥔  ︶︶⊹︶\n"
        f"⊹ ࣪ ˖  **Hobbies;** {hobbies}\n"
        f"⊹ ࣪ ˖  **Gustos;** {gustos}\n"
        f"⊹ ࣪ ˖  **Disgustos;** {disgustos}\n"
        "╰─────────────  ✦ ⁺."
    )

def format_teacher_sheet(data: dict) -> str:
    hobbies   = data.get("hobbies",   "No especificado")
    gustos    = data.get("gustos",    "No especificado")
    disgustos = data.get("disgustos", "No especificado")

    return (
        "╭─────┈╯  𓈃  ⋆ ࣪.  🔮 ◌Ⳋ𝅄\n"
        " 💌     ࣪  𝑫𝒆𝒂𝒓 ࣪  ᚐ  ִ  𝑻𝒆𝒂𝒄𝒉𝒆𝒓 ބ  ࣪\n"
        f"⊹ ࣪ ˖           __{data['personaje']}__ ✶  __{data['edad']}__ ˚. ᵎᵎ\n"
        f"⊹ ࣪ ˖           __{data['especie']}__ ✶  __{data['pronouns']}__ ˚. ᵎᵎ\n"
        f"⊹ ࣪ ˖           __{data['elemento']}__ ✶ __{data['clase']}__ ˚. ᵎᵎ\n"
        "︶⊹︶︶⠀𖥔  ︶︶⊹︶\n"
        f"⊹ ࣪ ˖  **Poderes/Habilidades;** {data['habilidades']}\n"
        f"⊹ ࣪ ˖  **Debilidades;** {data['debilidades']}\n"
        "︶⊹︶︶⠀𖥔  ︶︶⊹︶\n"
        f"⊹ ࣪ ˖  **Personalidad;** {data['personalidad']}\n"
        f"⊹ ࣪ ˖  **Historia;** {data['historia']}\n"
        "︶⊹︶︶⠀𖥔  ︶︶⊹︶\n"
        f"⊹ ࣪ ˖  **Hobbies;** {hobbies}\n"
        f"⊹ ࣪ ˖  **Gustos;** {gustos}\n"
        f"⊹ ࣪ ˖  **Disgustos;** {disgustos}\n"
        "╰─────────────  ✦ ⁺."
    )

def format_worker_sheet(data: dict) -> str:
    hobbies   = data.get("hobbies",   "No especificado")
    gustos    = data.get("gustos",    "No especificado")
    disgustos = data.get("disgustos", "No especificado")

    return (
        "╭─────┈╯  𓈃  ⋆ ࣪.  🔮 ◌Ⳋ𝅄\n"
        " 💌     ࣪  𝑫𝒆𝒂𝒓 ࣪  ᚐ  ִ  𝑾𝒐𝒓𝒌𝒆𝒓 ބ  ࣪\n"
        f"⊹ ࣪ ˖           __{data['personaje']}__ ✶  __{data['edad']}__ ˚. ᵎᵎ\n"
        f"⊹ ࣪ ˖           __{data['especie']}__ ✶  __{data['pronouns']}__ ˚. ᵎᵎ\n"
        f"⊹ ࣪ ˖           __{data['elemento']}__ ✶ __{data['cargo']}__ ˚. ᵎᵎ\n"
        "︶⊹︶︶⠀𖥔  ︶︶⊹︶\n"
        f"⊹ ࣪ ˖  **Poderes/Habilidades;** {data['habilidades']}\n"
        f"⊹ ࣪ ˖  **Debilidades;** {data['debilidades']}\n"
        "︶⊹︶︶⠀𖥔  ︶︶⊹︶\n"
        f"⊹ ࣪ ˖  **Personalidad;** {data['personalidad']}\n"
        f"⊹ ࣪ ˖  **Historia;** {data['historia']}\n"
        "︶⊹︶︶⠀𖥔  ︶︶⊹︶\n"
        f"⊹ ࣪ ˖  **Hobbies;** {hobbies}\n"
        f"⊹ ࣪ ˖  **Gustos;** {gustos}\n"
        f"⊹ ࣪ ˖  **Disgustos;** {disgustos}\n"
        "╰─────────────  ✦ ⁺."
    )

# ──────────────────────────────────────────────
# EMBED DE REVISIÓN STAFF
# ──────────────────────────────────────────────

def build_review_embed(tipo: str, data: dict, color=None) -> discord.Embed:
    if color is None: color = COLOR_PENDIENTE
    titulos = {
        "uniforme":   "👕 Nuevo Uniforme",
        "estudiante": "🎓 Ficha de Estudiante",
        "profesor":   "🧑‍🏫 Ficha de Profesor",
        "trabajador": "🧑‍💼 Ficha de Trabajador",
    }
    embed = discord.Embed(title=titulos.get(tipo, "📋 Nueva Ficha"), color=color)
    embed.set_footer(text=f"User ID: {data.get('user_id')} • {data.get('username','???')}")
    embed.add_field(name="Personaje", value=data.get("personaje","—"), inline=True)

    if tipo == "uniforme":
        if data.get("imagen"): embed.set_image(url=data["imagen"])
        return embed

    embed.add_field(name="Edad",       value=data.get("edad","—"),     inline=True)
    embed.add_field(name="Pronombres", value=data.get("pronouns","—"), inline=True)
    embed.add_field(name="Especie",    value=data.get("especie","—"),  inline=True)
    embed.add_field(name="Elemento",   value=data.get("elemento","—"), inline=True)

    if tipo == "profesor":
        embed.add_field(name="Clase",  value=data.get("clase","—"), inline=True)
    if tipo == "trabajador":
        embed.add_field(name="Cargo",  value=data.get("cargo","—"), inline=True)
    if tipo == "estudiante":
        clubes = data.get("clubes_nombres", data.get("club","—"))
        if isinstance(clubes, list): clubes = ", ".join(clubes) if clubes else "Ninguno"
        embed.add_field(name="Club(es)",  value=clubes,                    inline=True)
        embed.add_field(name="Hobbies",   value=data.get("hobbies","—"),   inline=False)
        embed.add_field(name="Gustos",    value=data.get("gustos","—"),    inline=True)
        embed.add_field(name="Disgustos", value=data.get("disgustos","—"), inline=True)

    embed.add_field(name="⚔️ Habilidades", value=data.get("habilidades","—")[:1024], inline=False)
    embed.add_field(name="🩹 Debilidades", value=data.get("debilidades","—")[:1024], inline=False)
    embed.add_field(name="🧠 Personalidad",value=data.get("personalidad","—")[:1024],inline=False)
    embed.add_field(name="📖 Historia",    value=data.get("historia","—")[:1024],    inline=False)

    if data.get("imagen"): embed.set_image(url=data["imagen"])
    return embed

# ──────────────────────────────────────────────
# CARTA DE ACEPTACIÓN — Morado
# ──────────────────────────────────────────────

def build_acceptance_embed(tipo: str, personaje: str, user_id: int,
                           conteo: dict, gen: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"💌 Carta de Aceptación — {personaje}",
        description=(
            f"¡Felicidades! Tu personaje, **{personaje}**, ha sido oficialmente aceptado "
            f"en la Academia Arcana de Isefora.\n\n"
            f"Esperamos que disfrutes tu trayectoria académica y que cada rincón de Isefora "
            f"te inspire a alcanzar tu máximo potencial.\n\n"
            f"*Atentamente, La Administración de la Academia.*"
        ),
        color=COLOR_ACEPTACION
    )
    embed.add_field(name="Tipo",       value=tipo.capitalize(), inline=True)
    embed.add_field(name="Generación", value=f"Gen {gen}",      inline=True)
    embed.add_field(
        name="📊 Tus personajes en esta generación",
        value=(
            f"🎓 Estudiantes: **{conteo.get('estudiantes_usados', 0)}**\n"
            f"🧑‍🏫 Profesores: **{conteo.get('profesores_usados', 0)}**\n"
            f"🧑‍💼 Trabajadores: **{conteo.get('trabajadores_usados', 0)}**"
        ),
        inline=False
    )
    if conteo.get("slots_extra_disponibles", 0) > 0 or conteo.get("slots_extra_usados", 0) > 0:
        embed.add_field(
            name="✨ Slots adicionales",
            value=(
                f"Disponibles: **{conteo.get('slots_extra_disponibles', 0)}**\n"
                f"Usados: **{conteo.get('slots_extra_usados', 0)}**"
            ),
            inline=False
        )
    return embed

# ──────────────────────────────────────────────
# PUBLICAR FICHA CON TODAS LAS IMÁGENES
# ──────────────────────────────────────────────

async def publicar_ficha_con_imagenes(canal: discord.TextChannel, texto: str, data: dict):
    await canal.send(texto)
    urls = []
    if data.get("imagen"): urls.append(data["imagen"])
    for url in data.get("imagenes", []):
        if url and url not in urls: urls.append(url)
    for url in urls:
        try:
            e = discord.Embed(color=COLOR_INFO)
            e.set_image(url=url)
            await canal.send(embed=e)
        except Exception:
            pass
