import os
import sys
import time
import traceback
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("[ERROR] La variable de entorno TELEGRAM_BOT_TOKEN no está configurada en Backend/.env")
    print("Por favor, crea tu bot con @BotFather y agrega el token al archivo .env")
    sys.exit(1)

BOT_URL = f"https://api.telegram.org/bot{TOKEN}"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Importar sesión de base de datos y modelos del proyecto
# Añadimos el directorio actual al path para importar correctamente app
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.models.user_model import User
from app.controllers.pet_health_controller import get_user_pets
from app.models.pet_medical_card_model import PetMedicalCard
from app.models.pet_reminder_model import PetReminder

# Importación opcional de ollama
try:
    # pyrefly: ignore [missing-import]
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    ollama = None
    OLLAMA_AVAILABLE = False
    print("[WARNING] La librería 'ollama' no está instalada. El bot no podrá responder preguntas usando IA.")

def send_message(chat_id, text):
    """Enviar un mensaje al chat de Telegram"""
    url = f"{BOT_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] No se pudo enviar mensaje a {chat_id}: {e}")

def link_user(chat_id, user_id_str):
    """Vincular el telegram_chat_id con el usuario de PetHouse"""
    try:
        user_id = int(user_id_str)
    except ValueError:
        return "⚠️ El enlace de vinculación no es válido."

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.deleted_at == None).first()
        if not user:
            return "❌ No se encontró ningún usuario con ese ID en PetHouse."
        
        # Guardar chat ID
        user.telegram_chat_id = str(chat_id)
        db.commit()
        
        return f"🎉 ¡Hola {user.name}! Tu cuenta de PetHouse ha sido vinculada exitosamente a este chat.\n\nRecibirás aquí los recordatorios de tus mascotas y puedes hacerme cualquier consulta sobre ellas. 🐾"
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error vinculando usuario {user_id}: {e}")
        return "❌ Ocurrió un error al vincular tu cuenta en la base de datos."
    finally:
        db.close()

def get_rag_context(chat_id):
    """Recuperar la información de las mascotas, fichas médicas y recordatorios del usuario (Retrieval)"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == str(chat_id), User.deleted_at == None).first()
        if not user:
            return None, "No vinculado"
        
        # Obtener mascotas usando la lógica del controlador de PetHouse
        user_pets = get_user_pets(db, user.id)
        
        if not user_pets:
            return user, "El usuario no tiene mascotas registradas todavía en PetHouse."
        
        context = f"Usuario: {user.name} {user.last_name}\n"
        context += "Mascotas registradas en PetHouse:\n"
        
        for pet in user_pets:
            context += f"\n- Nombre: {pet.name}\n"
            context += f"  Especie: {pet.species or 'Desconocida'}, Raza: {pet.race or 'Desconocida'}, Género: {pet.gender or 'Desconocido'}\n"
            
            # Lecturas defensivas: evitamos funciones que alteran esquema durante el flujo de Telegram.
            try:
                card = (
                    db.query(PetMedicalCard)
                    .filter(PetMedicalCard.pet_id == pet.id, PetMedicalCard.deleted_at == None)
                    .first()
                )
                if card:
                    context += f"  Ficha Médica: Tipo de sangre: {card.blood_type or 'No registrado'}, Alergias: {card.allergies or 'Ninguna'}, Condiciones médicas: {card.conditions or 'Ninguna'}, Observaciones: {card.observations or 'Ninguna'}\n"
                else:
                    context += "  Ficha Médica: No tiene ficha médica registrada todavía.\n"
            except Exception as e:
                print(f"[WARNING] No se pudo leer ficha médica de pet_id={pet.id}: {e}")
                context += "  Ficha Médica: Temporalmente no disponible por un problema de conexión.\n"

            try:
                reminders = (
                    db.query(PetReminder)
                    .filter(PetReminder.pet_id == pet.id, PetReminder.deleted_at == None)
                    .order_by(PetReminder.fecha.asc())
                    .all()
                )
                pending = [r for r in reminders if (r.status or "").lower() == "pendiente"]
                if pending:
                    context += "  Recordatorios Pendientes:\n"
                    for r in pending:
                        fecha_str = r.fecha.strftime('%d/%m/%Y') if r.fecha else 'Sin fecha'
                        context += f"    * [{r.type}] programado para el {fecha_str} (Notas: {r.notes or 'Ninguna'})\n"
                else:
                    context += "  Recordatorios Pendientes: Ninguno registrado.\n"
            except Exception as e:
                print(f"[WARNING] No se pudieron leer recordatorios de pet_id={pet.id}: {e}")
                context += "  Recordatorios Pendientes: Temporalmente no disponibles por un problema de conexión.\n"
                
        return user, context
    except Exception as e:
        print(f"[ERROR] Error obteniendo contexto RAG para chat {chat_id}: {e}")
        traceback.print_exc()
        return None, "Error de base de datos"
    finally:
        db.close()

def query_ollama_rag(context, query):
    """Consultar a Ollama usando la información recuperada de la BD como contexto (Generation)"""
    if not OLLAMA_AVAILABLE:
        return "⚠️ El asistente de IA (Ollama) no está disponible en este servidor. Solo puedo enviar alertas automatizadas."

    system_prompt = f"""
    Eres Togo, el asistente virtual de IA de PetHouse. Tu objetivo es responder dudas sobre las mascotas del usuario.
    
    Tienes acceso a la siguiente información REAL de las mascotas del usuario (Contexto RAG):
    ------------------
    {context}
    ------------------
    
    Instrucciones críticas:
    1. Responde a la pregunta del usuario utilizando ÚNICAMENTE los datos provistos en el contexto anterior.
    2. Si el usuario te pregunta por algo de su mascota que NO está en el contexto (por ejemplo, vacunas que no figuran o alergias no mencionadas), dile de forma amigable que no tienes ese dato registrado en PetHouse.
    3. Mantén respuestas concisas, amables y utiliza emojis adecuados (🐾, 🐶, 🐱, ❤️).
    4. Responde en español de forma natural y lo más conciso posible.
    """
    
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt.strip()},
                {'role': 'user', 'content': query}
            ],
            options={
                'temperature': 0.5,
                'top_p': 0.9,
                'num_predict': 250
            }
        )
        return response['message']['content']
    except Exception as e:
        print(f"[ERROR] Error al invocar Ollama (host={OLLAMA_HOST}, model={OLLAMA_MODEL}): {e}")
        return "🐾 Lo siento, estoy teniendo problemas para procesar tu consulta con mi IA. ¿Puedes intentar más tarde?"

def handle_message(chat_id, text):
    """Manejar mensajes entrantes en Telegram"""
    text_clean = text.strip()
    
    # Manejar comando /start
    if text_clean.startswith("/start"):
        parts = text_clean.split()
        if len(parts) > 1:
            # Viene con token de vinculación: /start user_id
            response_msg = link_user(chat_id, parts[1])
            send_message(chat_id, response_msg)
        else:
            # Inicio normal
            welcome_msg = (
                "👋 ¡Hola! Soy Togo, el asistente virtual de **PetHouse**.\n\n"
                "Para recibir aquí tus recordatorios de salud y hacerme preguntas sobre tus mascotas, "
                "debes vincular tu cuenta. Inicia sesión en la plataforma web de PetHouse y haz clic en el botón 'Vincular Telegram'. 🐾"
            )
            send_message(chat_id, welcome_msg)
        return

    # Consultar contexto RAG
    user, context = get_rag_context(chat_id)
    
    if context == "No vinculado":
        not_linked_msg = (
            "⚠️ Aún no has vinculado tu cuenta de PetHouse con este chat.\n\n"
            "Para hacerlo, ingresa a la plataforma web de PetHouse y haz clic en el botón 'Vincular Telegram'."
        )
        send_message(chat_id, not_linked_msg)
        return
        
    if context == "Error de base de datos":
        send_message(chat_id, "❌ Hubo un error de conexión al buscar tus mascotas. Por favor, intenta de nuevo.")
        return

    # Responder con RAG
    reply = query_ollama_rag(context, text_clean)
    send_message(chat_id, reply)

def main():
    print("=" * 50)
    print("🤖 PetHouse Telegram RAG Bot está ejecutándose...")
    print("Presiona Ctrl+C para detener.")
    print("=" * 50)
    
    offset = 0
    while True:
        try:
            # Consultas a Telegram Bot API (polling) con timeout de 30 segundos
            url = f"{BOT_URL}/getUpdates"
            params = {"offset": offset, "timeout": 30}
            r = requests.get(url, params=params, timeout=35)
            
            if r.status_code == 200:
                data = r.json()
                if "result" in data:
                    for update in data["result"]:
                        update_id = update["update_id"]
                        offset = update_id + 1
                        
                        if "message" in update and "text" in update["message"]:
                            chat_id = update["message"]["chat"]["id"]
                            text = update["message"]["text"]
                            print(f"[Mensaje recibido] Chat ID: {chat_id} -> {text[:30]}...")
                            handle_message(chat_id, text)
            else:
                print(f"[WARNING] Error en polling. Status code: {r.status_code}")
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\nBot detenido por el usuario.")
            break
        except Exception as e:
            print(f"[ERROR] Ocurrió un error en el bucle principal: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
