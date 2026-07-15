import re


def limpiar_respuesta(texto: str) -> str:
    """
    Limpia la respuesta generada por la IA.
    """

    reemplazos = [
        ("**", ""),
        ("###", ""),
        ("##", ""),
        ("```", ""),
        ("`", ""),
    ]

    for viejo, nuevo in reemplazos:
        texto = texto.replace(viejo, nuevo)

    # Elimina saltos de línea excesivos
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto.strip()