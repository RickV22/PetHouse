import os
import sys
import time
import traceback
import datetime
from sqlalchemy import func
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(override=True)


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("[ERROR] La variable de entorno TELEGRAM_BOT_TOKEN no está configurada en Backend/.env")
    print("Por favor, crea tu bot con @BotFather y agrega el token al archivo .env")
    sys.exit(1)

BOT_URL = f"https://api.telegram.org/bot{TOKEN}"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_MODEL_VISION = os.getenv("OLLAMA_MODEL_VISION", "moondream")

# Importar sesión de base de datos y modelos del proyecto
# Añadimos el directorio actual al path para importar correctamente app
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.models.user_model import User
from app.controllers.pet_health_controller import get_user_pets
from app.models.pet_medical_card_model import PetMedicalCard
from app.models.pet_reminder_model import PetReminder
from app.models.veterinary_chat_history_model import VeterinaryChatHistory

# Importación opcional de ollama
try:
    # pyrefly: ignore [missing-import]
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    ollama = None
    OLLAMA_AVAILABLE = False
    print("[WARNING] La librería 'ollama' no está instalada. El bot no podrá responder preguntas usando IA.")

# Importación de pypdf
try:
    # pyrefly: ignore [missing-import]
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PdfReader = None
    PYPDF_AVAILABLE = False
    print("[WARNING] La librería 'pypdf' no está instalada. El bot no podrá procesar archivos PDF.")


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


def _get_due_reminder_notifications(reminders, now=None):
    """Devuelve los recordatorios que deben notificarse como hoy o mañana, incluyendo la ventana previa de 10 minutos."""
    if now is None:
        now = time.time()
        if isinstance(now, float):
            now = datetime.datetime.fromtimestamp(now)

    if not hasattr(now, "date"):
        now = datetime.datetime.fromtimestamp(now)

    today = now.date()
    tomorrow = today + datetime.timedelta(days=1)
    due = []

    for reminder in reminders:
        if not reminder.fecha:
            continue
        if (reminder.status or "").lower() == "notificado":
            continue

        reminder_dt = reminder.fecha if isinstance(reminder.fecha, datetime.datetime) else datetime.datetime.combine(reminder.fecha, datetime.time.min)
        reminder_date = reminder_dt.date()
        window_start = reminder_dt - datetime.timedelta(minutes=10)
        window_end = reminder_dt + datetime.timedelta(minutes=10)

        if reminder_date == today and now >= window_start and now <= window_end:
            due.append((reminder, "hoy"))
        elif reminder_date == tomorrow:
            due.append((reminder, "mañana"))

    return due


def send_reminder_notifications():
    """Envía notificaciones de Telegram para recordatorios pendientes de hoy y mañana."""
    db = SessionLocal()
    try:
        reminders = (
            db.query(PetReminder)
            .filter(PetReminder.deleted_at == None)
            .filter((PetReminder.status == None) | (func.lower(PetReminder.status) != "notificado"))
            .all()
        )

        now = datetime.datetime.utcnow()
        due_reminders = _get_due_reminder_notifications(reminders, now=now)
        for reminder, when in due_reminders:
            pet = reminder.pet
            user = db.query(User).filter(User.id == pet.publisher_id, User.deleted_at == None).first()
            if not user or not user.telegram_chat_id:
                continue

            fecha_str = reminder.fecha.strftime("%d/%m/%Y") if reminder.fecha else "Sin fecha"
            if when == "ahora":
                when_label = "en este momento"
            elif when == "hoy":
                when_label = "hoy"
            elif when == "mañana":
                when_label = "mañana"
            else:
                when_label = when

            message = (
                f"🔔 Recordatorio de PetHouse\n\n"
                f"Tu mascota *{pet.name}* tiene un recordatorio para {when_label}:\n"
                f"📌 Tipo: *{reminder.type}*\n"
                f"📅 Fecha: *{fecha_str}*\n"
            )
            if reminder.notes:
                message += f"📝 Notas: *{reminder.notes}*\n"
            message += "\nCuida a tu mascota con tiempo. 🐾"
            send_message(user.telegram_chat_id, message)
            reminder.status = "notificado"

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error enviando recordatorios de Telegram: {e}")
    finally:
        db.close()


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

def download_telegram_file(file_id, dest_path):
    """Descargar un archivo desde la API de Telegram y guardarlo localmente"""
    url = f"{BOT_URL}/getFile"
    payload = {"file_id": file_id}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            file_info = r.json()
            if file_info.get("ok"):
                file_path = file_info["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                file_data = requests.get(download_url, timeout=30)
                if file_data.status_code == 200:
                    # Crear directorio si no existe
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    with open(dest_path, "wb") as f:
                        f.write(file_data.content)
                    return True
        print(f"[WARNING] No se pudo descargar el archivo con file_id={file_id}. Status={r.status_code}")
    except Exception as e:
        print(f"[ERROR] Error al descargar archivo de Telegram: {e}")
    return False

def extract_text_from_pdf(pdf_path):
    """Extraer el texto de un archivo PDF usando pypdf"""
    if not PYPDF_AVAILABLE or not PdfReader:
        return "⚠️ (Error: La librería 'pypdf' no está instalada en el servidor, no se pudo leer el PDF)."
    
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Página {i+1} ---\n{page_text}\n"
        return text.strip()
    except Exception as e:
        print(f"[ERROR] Error al leer PDF en {pdf_path}: {e}")
        return f"⚠️ (Error al procesar el archivo PDF: {e})"

def resolve_pet_id(db, user_id, text):
    """Heurística para encontrar a qué mascota se refiere la conversación"""
    try:
        # Obtener mascotas usando la lógica del controlador de PetHouse
        user_pets = get_user_pets(db, user_id)
        if not user_pets:
            return None
            
        text_lower = text.lower()
        # Buscar coincidencia exacta del nombre de la mascota
        for pet in user_pets:
            if pet.name.lower() in text_lower:
                return pet.id
                
        # Si el usuario solo tiene una mascota, asumimos que habla de ella
        if len(user_pets) == 1:
            return user_pets[0].id
            
        return None
    except Exception as e:
        print(f"[ERROR] Error resolviendo pet_id: {e}")
        return None

def get_chat_history(db, user_id, limit=8):
    """Obtener el historial de conversación reciente para dar memoria al agente"""
    try:
        history = (
            db.query(VeterinaryChatHistory)
            .filter(VeterinaryChatHistory.user_id == user_id)
            .order_by(VeterinaryChatHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        # Devolver en orden cronológico (el más antiguo primero)
        return list(reversed(history))
    except Exception as e:
        print(f"[ERROR] Error al recuperar historial de chat: {e}")
        return []

def save_chat_interaction(db, user_id, pet_id, question, answer):
    """Guardar la interacción en la tabla veterinary_chat_history"""
    try:
        new_chat = VeterinaryChatHistory(
            user_id=user_id,
            pet_id=pet_id,
            question=question,
            answer=answer,
            created_at=datetime.datetime.utcnow()
        )
        db.add(new_chat)
        db.commit()
        print(f"[DB] Interacción guardada en historial para user_id={user_id}, pet_id={pet_id}")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] No se pudo guardar la interacción en la base de datos: {e}")

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

def query_ollama_rag(context, query, history=None, images=None):
    """Consultar a Ollama usando la información recuperada de la BD como contexto (Generation)"""
    if not OLLAMA_AVAILABLE:
        return "⚠️ El asistente de IA (Ollama) no está disponible en este servidor. Solo puedo enviar alertas automatizadas."

    system_prompt = f"""
    Eres Togo, el asistente virtual de IA de PetHouse. Tu objetivo es responder dudas sobre las mascotas del usuario y analizar documentos (como PDFs o imágenes clínicas) que el usuario te envíe.
    Si el usuario pregunta si puedes analizar un PDF, documento o imagen, debes responder que sí puedes analizarlo y que el usuario debe enviarlo para poder analizarlo.
    Tienes acceso a la siguiente información REAL de las mascotas del usuario (Contexto RAG):
    ------------------
    {context}
    ------------------
    
    Instrucciones críticas:
    1. Responde a la pregunta del usuario utilizando los datos provistos en el contexto de las mascotas, los archivos adjuntos (si los hay) y el historial de conversación.
    2. Si el usuario te pregunta por algo de su mascota que NO está en el contexto ni en los archivos/conversación (por ejemplo, vacunas que no figuran o alergias no mencionadas), dile de forma amigable que no tienes ese dato registrado en PetHouse.
    3. Mantén respuestas concisas, amables y utiliza emojis adecuados (🐾, 🐶, 🐱, ❤️).
    4. Responde en español de forma natural y lo más conciso posible.
    """
    
    messages = [
        {'role': 'system', 'content': system_prompt.strip()}
    ]
    
    # Agregar historial si existe
    if history:
        for interaction in history:
            messages.append({'role': 'user', 'content': interaction.question})
            messages.append({'role': 'assistant', 'content': interaction.answer})
            
    # Agregar mensaje actual
    if images:
        vision_query = query
        if "español" not in vision_query.lower() and "espanol" not in vision_query.lower():
            vision_query = f"RESPONDE EN ESPAÑOL: {vision_query}"
        user_msg = {'role': 'user', 'content': vision_query, 'images': images}
    else:
        user_msg = {'role': 'user', 'content': query}
        
    messages.append(user_msg)
    
    # Usar modelo de visión si hay imágenes, de lo contrario usar el modelo estándar
    model_to_use = OLLAMA_MODEL_VISION if images else OLLAMA_MODEL

    try:
        client = ollama.Client(host=OLLAMA_HOST)
        response = client.chat(
            model=model_to_use,
            messages=messages,
            options={
                'temperature': 0.5,
                'top_p': 0.9,
                'num_predict': 400
            }
        )
        return response['message']['content']
    except Exception as e:
        print(f"[ERROR] Error al invocar Ollama (host={OLLAMA_HOST}, model={model_to_use}): {e}")
        if images and ("vision" in str(e).lower() or "image" in str(e).lower() or "format" in str(e).lower()):
            return f"⚠️ Recibí tu imagen, pero el modelo de IA de visión configurado (`{model_to_use}`) no parece responder correctamente o no está descargado. Asegúrate de haber ejecutado 'ollama pull {model_to_use}' en tu servidor Ollama."
        return "🐾 Lo siento, estoy teniendo problemas para procesar tu consulta con mi IA. ¿Puedes intentar más tarde?"


def handle_message(chat_id, text="", photo=None, document=None):
    """Manejar mensajes entrantes en Telegram, incluyendo textos, fotos y documentos"""
    text_clean = text.strip() if text else ""
    
    # Manejar comando /start (solo si no se enviaron archivos)
    if text_clean.startswith("/start") and not photo and not document:
        parts = text_clean.split()
        if len(parts) > 1:
            response_msg = link_user(chat_id, parts[1])
            send_message(chat_id, response_msg)
        else:
            welcome_msg = (
                "👋 ¡Hola! Soy Togo, el asistente virtual de **PetHouse**.\n\n"
                "Para recibir aquí tus recordatorios de salud y hacerme preguntas sobre tus mascotas, "
                "debes vincular tu cuenta. Inicia sesión en la plataforma web de PetHouse, ve a la sección de veterinario y haz clic en el botón 'Vincular Telegram'. 🐾"
            )
            send_message(chat_id, welcome_msg)
        return

    # Consultar contexto RAG
    user, context = get_rag_context(chat_id)
    
    if context == "No vinculado":
        not_linked_msg = (
            "⚠️ Aún no has vinculado tu cuenta de PetHouse con este chat.\n\n"
            "Para hacerlo, ingresa a la plataforma web de PetHouse, ve a la sección de veterinario y haz clic en el botón 'Vincular Telegram'."
        )
        send_message(chat_id, not_linked_msg)
        return
        
    if context == "Error de base de datos":
        send_message(chat_id, "❌ Hubo un error de conexión al buscar tus mascotas. Por favor, intenta de nuevo.")
        return

    # Inicializar variables para archivos temporales e imágenes
    temp_file_path = None
    images_list = []
    current_query = text_clean
    
    db = SessionLocal()
    try:
        # 1. Procesar Documento (PDF)
        if document:
            file_name = document.get("file_name", "")
            mime_type = document.get("mime_type", "")
            
            if mime_type == "application/pdf" or file_name.lower().endswith(".pdf"):
                send_message(chat_id, f"📄 Estoy analizando tu PDF *{file_name}*... Por favor espera un momento.")
                
                file_id = document["file_id"]
                # Crear nombre temporal único
                temp_file_path = os.path.abspath(os.path.join("temp", f"tg_doc_{file_id}.pdf"))
                
                if download_telegram_file(file_id, temp_file_path):
                    pdf_text = extract_text_from_pdf(temp_file_path)
                    
                    if pdf_text:
                        if current_query:
                            current_query = (
                                f"[Archivo PDF adjunto: {file_name}]\n"
                                f"Contenido del PDF:\n{pdf_text}\n\n"
                                f"Pregunta del usuario sobre el PDF:\n{current_query}"
                            )
                        else:
                            current_query = (
                                f"[Archivo PDF adjunto: {file_name}]\n"
                                f"Contenido del PDF:\n{pdf_text}\n\n"
                                f"Por favor, analiza este documento PDF, resume sus puntos más importantes "
                                f"y explica si contiene información sobre la salud o cuidados de una mascota."
                            )
                    else:
                        send_message(chat_id, "⚠️ No se pudo extraer texto del PDF (tal vez esté vacío o escaneado como imagen). Intentaré responder con el texto disponible.")
                else:
                    send_message(chat_id, "❌ Error al descargar el archivo PDF de los servidores de Telegram.")
            else:
                send_message(chat_id, "⚠️ Por ahora solo puedo procesar archivos de tipo PDF. Envía un PDF válido para poder leerlo.")
                return

        # 2. Procesar Foto (Imagen)
        elif photo:
            largest_photo = photo[-1]
            file_id = largest_photo["file_id"]
            
            send_message(chat_id, "Estoy analizando tu imagen... Por favor espera un momento.")
            
            temp_file_path = os.path.abspath(os.path.join("temp", f"tg_img_{file_id}.jpg"))
            
            if download_telegram_file(file_id, temp_file_path):
                images_list.append(temp_file_path)
                if not current_query:
                    current_query = "analiza la imagen y responde de acuerdo lo que el usuario pregunte sobre ella."
                else:
                    # Asegurar formato de pregunta si es necesario
                    if not current_query.endswith("?") and not current_query.endswith("."):
                        current_query = f"¿{current_query}?"
            else:
                send_message(chat_id, "❌ Error al descargar la imagen de los servidores de Telegram.")
                return

        # Si no hay consulta ni archivos, no hacemos nada
        if not current_query and not photo and not document:
            return

        # 3. Obtener Historial de Chat (Memoria)
        history = get_chat_history(db, user.id, limit=8)

        # 4. Consultar a Ollama con Contexto RAG, Historial y Archivos
        reply = query_ollama_rag(context, current_query, history=history, images=images_list)
        
        # Enviar respuesta
        send_message(chat_id, reply)

        # 5. Guardar en Historial de Chat (veterinary_chat_history)
        pet_id = resolve_pet_id(db, user.id, text_clean if text_clean else current_query)
        
        saved_question = text_clean
        if not saved_question:
            if document:
                saved_question = f"[Envió PDF: {document.get('file_name', 'documento.pdf')}]"
            elif photo:
                saved_question = "[Envió una imagen]"
            else:
                saved_question = "Consulta sin texto"
        else:
            if document:
                saved_question = f"[PDF: {document.get('file_name', 'documento.pdf')}] {saved_question}"
            elif photo:
                saved_question = f"[Imagen] {saved_question}"
                
        save_chat_interaction(db, user.id, pet_id, saved_question, reply)

    except Exception as e:
        print(f"[ERROR] Error manejando el mensaje en el bot: {e}")
        traceback.print_exc()
        send_message(chat_id, "❌ Ocurrió un error inesperado al procesar tu solicitud. Por favor, intenta nuevamente.")
    finally:
        db.close()
        # Eliminar archivo temporal
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"[TEMP] Archivo temporal eliminado: {temp_file_path}")
            except Exception as e:
                print(f"[WARNING] No se pudo eliminar el archivo temporal {temp_file_path}: {e}")


def main():
    print("=" * 50)
    print("🤖 PetHouse Telegram RAG Bot está ejecutándose...")
    print("Presiona Ctrl+C para detener.")
    print("=" * 50)
    
    offset = 0
    while True:
        try:
            send_reminder_notifications()
        except Exception as e:
            print(f"[WARNING] No se pudieron enviar recordatorios automáticos: {e}")

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
                        
                        if "message" in update:
                            msg = update["message"]
                            chat_id = msg.get("chat", {}).get("id")
                            if not chat_id:
                                continue
                                
                            text = msg.get("text") or msg.get("caption") or ""
                            photo = msg.get("photo")
                            document = msg.get("document")
                            
                            if text or photo or document:
                                print(f"[Mensaje recibido] Chat ID: {chat_id} | Texto: {text[:20]}... | Foto: {bool(photo)} | Doc: {bool(document)}")
                                handle_message(chat_id, text=text, photo=photo, document=document)
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
