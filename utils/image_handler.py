# utils/image_handler.py
# Estado de espera de imágenes — un solo listener en bot.py lo procesa todo.

_esperando: dict = {}

def registrar_espera(user_id: int, tipo: str, canal_id: int, data: dict):
    _esperando[user_id] = {"tipo": tipo, "canal_id": canal_id, "data": data}

def cancelar_espera(user_id: int):
    _esperando.pop(user_id, None)

def get_espera(user_id: int) -> dict | None:
    return _esperando.get(user_id)

def esta_esperando(user_id: int, canal_id: int) -> bool:
    e = _esperando.get(user_id)
    return e is not None and e["canal_id"] == canal_id
