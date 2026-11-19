APP_NAME = "Asistente HAZMAT"
APP_VERSION = "5.4.0"  # visible en el pie de acceso: delata servidores desactualizados
APP_SUBTITLE = "Bomberos de Chile · GRE 2024"
APP_ICON = ":material/local_fire_department:"

# (ícono Material, texto visible, consulta enviada)
SUGGESTIONS = [
    (
        ":material/search:",
        "¿Qué guía corresponde al UN 1203?",
        "¿Qué guía corresponde al UN 1203?",
    ),
    (
        ":material/radar:",
        "Distancias de aislamiento para cloro (UN 1017)",
        "Distancia de aislamiento y evacuación para cloro UN 1017",
    ),
    (
        ":material/emergency:",
        "Fuga de amoniaco en planta frigorífica: plan de respuesta",
        "Fuga de amoniaco anhidro en una planta frigorífica con nube visible, ¿cómo respondo?",
    ),
    (
        ":material/health_and_safety:",
        "EPP para un derrame de ácido sulfúrico",
        "¿Qué EPP necesito para un derrame de ácido sulfúrico?",
    ),
]

LEVEL_LABELS = {
    "low": "Nivel bajo",
    "medium": "Nivel medio",
    "high": "Nivel alto",
}

ROLE_LABELS = {"admin": "Administrador", "operador": "Operador"}
