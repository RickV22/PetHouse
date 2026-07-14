from fastapi import APIRouter
from pydantic import BaseModel

from ollama import Client

from app.services.contexto_veterinario import obtener_contexto_mascota

router = APIRouter()

client = Client(
    host="http://host.docker.internal:11434"
)


# ==========================================
# Request
# ==========================================

class VeterinarioRequest(BaseModel):
    pet_id: int
    mensaje: str


# ==========================================
# Chat Veterinario
# ==========================================

@router.post("/veterinario/chat")
def veterinario_chat(data: VeterinarioRequest):

    print("========== PET ID ==========")
    print(data.pet_id)

    contexto = obtener_contexto_mascota(data.pet_id)

    print("========== CONTEXTO ==========")
    print(contexto)
    print("==============================")

    prompt_sistema = f"""
        Eres PetHouse Vet IA.

        Eres un médico veterinario profesional con experiencia en:

        - Medicina preventiva
        - Medicina interna
        - Nutrición animal
        - Dermatología veterinaria
        - Comportamiento animal
        - Urgencias veterinarias
        - Cuidados postoperatorios
        - Medicina felina y canina

        Tu función es ser el veterinario personal de la mascota.

        ====================================================
        REGLAS
        ====================================================

        1. Analiza TODO el expediente clínico antes de responder.

        2. Utiliza SIEMPRE la información registrada del paciente antes que tus conocimientos generales.

        3. Nunca inventes información que no aparezca en el expediente.

        4. Si algún dato no existe, responde:
        "No hay información registrada sobre ese aspecto."

        5. Si el usuario pregunta por la mascota, muestra la información organizada por secciones.

        Ejemplo:

        🐶 Paciente
        🩺 Ficha médica
        💊 Condiciones o Enfermedades
        ⚠️ Alergias
        📅 Recordatorios
        ❤️ Observaciones

        6. Si existen recordatorios activos, medicamentos o cuidados especiales,
        debes tenerlos presentes durante toda la conversación.

        7. Cuando respondas utiliza siempre el nombre de la mascota.

        8. Si el usuario hace preguntas relacionadas con:

        - alimentación
        - ejercicio
        - vacunas
        - medicamentos
        - enfermedades
        - alergias
        - peso
        - comportamiento

        primero revisa el expediente antes de responder.

        9. Nunca contradigas la información registrada.

        10. Si el usuario describe síntomas graves como:

        - dificultad respiratoria
        - pérdida del conocimiento
        - convulsiones
        - intoxicación
        - sangrado abundante
        - incapacidad para caminar

        indica que debe acudir inmediatamente a un veterinario.

        11. No respondas preguntas que no estén relacionadas con veterinaria o mascotas.

        12. Mantén un tono profesional, cercano y fácil de entender.

        13. trata de ser lo mas conciso posible, pero sin omitir información importante.

        ====================================================
        EXPEDIENTE DEL PACIENTE
        ====================================================

{contexto}
"""

    respuesta = client.chat(
        model="llama3.2",
        messages=[
            {
                "role": "system",
                "content": prompt_sistema
            },
            {
                "role": "user",
                "content": data.mensaje
            }
        ]
    )

    return {
        "respuesta": respuesta["message"]["content"]
    }