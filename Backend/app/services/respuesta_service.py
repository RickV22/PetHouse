import re


def limpiar_respuesta(texto: str) -> str:
    """
    Limpia la respuesta generada por la IA.
    """

    # Elimina Markdown
    texto = texto.replace("**", "")
    texto = texto.replace("###", "")
    texto = texto.replace("##", "")
    texto = texto.replace("```", "")
    texto = texto.replace("`", "")

    # Elimina líneas compuestas únicamente por = - _
    texto = re.sub(r"^[=\-_]{3,}$", "", texto, flags=re.MULTILINE)

    # Elimina varios saltos de línea seguidos
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    # Elimina espacios repetidos
    texto = re.sub(r"[ \t]{2,}", " ", texto)

    return texto.strip()