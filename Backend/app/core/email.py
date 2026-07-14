import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_adoption_approval_email(user_email, user_name, pet_name):
    """
    Envía un correo electrónico al usuario notificando la aprobación de su adopción.
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        print("--- AVISO: No se enviará correo real (Faltan credenciales en .env) ---")
        return False

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = user_email
    msg['Subject'] = f"¡Felicidades! Tu solicitud para adoptar a {pet_name} ha sido aprobada"

    body = f"""
    Hola {user_name},

    ¡Es un placer informarte que tu solicitud de adopción para {pet_name} ha sido APROBADA! 🎉

    Estamos muy felices de que {pet_name} haya encontrado un hogar responsable como el tuyo.

    PRÓXIMOS PASOS:
    1. Acércate a nuestra casa de adopción en los próximos 3 días hábiles.
    2. Trae tu documento de identidad original.
    3. Trae una correa o guacal según corresponda para transportar a tu nuevo mejor amigo.

    UBICACIÓN:
    Casa PetHouse - Barranquilla, Colombia.
    Horario: Lunes a Sábado, 8:00 AM - 5:00 PM.

    Si tienes alguna duda adicional, puedes responder a este correo o llamarnos.

    ¡Te esperamos con mucha emoción!

    Atentamente,
    El equipo de PetHouse
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_user, user_email, text)
        server.quit()
        print(f"--- Correo de adopción enviado a {user_email} ---")
        return True
    except Exception as e:
        print(f"!!! ERROR CRÍTICO ENVIANDO CORREO ADOPCIÓN: {type(e).__name__}: {e}")
        return False


def _smtp_config():
    return (
        os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        int(os.getenv("SMTP_PORT", "587")),
        os.getenv("SMTP_USER"),
        os.getenv("SMTP_PASSWORD"),
    )


def _send(to_email: str, subject: str, body: str) -> bool:
    smtp_server, smtp_port, smtp_user, smtp_password = _smtp_config()
    if not smtp_user or not smtp_password:
        print("--- AVISO: No se enviará correo (Faltan SMTP_USER / SMTP_PASSWORD en .env) ---")
        return False
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        print(f"--- Correo enviado a {to_email}: {subject} ---")
        return True
    except Exception as e:
        print(f"!!! ERROR ENVIANDO CORREO: {type(e).__name__}: {e}")
        return False


def send_adoption_rejection_email(user_email: str, user_name: str, pet_name: str) -> bool:
    subject = f"Actualización sobre tu solicitud de adopción para {pet_name}"
    body = f"""Hola {user_name},

Lamentamos informarte que tu solicitud de adopción para {pet_name} ha sido RECHAZADA.

Esto puede deberse a que la documentación presentada estaba incompleta o la mascota ya fue asignada a otro solicitante.

Si crees que hubo un error, puedes contactarnos respondiendo a este correo.

Atentamente,
El equipo de PetHouse
"""
    return _send(user_email, subject, body)


def send_pet_submission_email(user_email: str, user_name: str, pet_name: str) -> bool:
    subject = f"Hemos recibido tu publicación de {pet_name}"
    body = f"""Hola {user_name},

Hemos recibido tu publicación de {pet_name} y la estamos revisando.

Nuestro equipo evaluará la información y te notificará por correo cuando la publicación sea aprobada o si necesitamos ajustes.

Gracias por ayudar a encontrar un hogar a una mascota.

Atentamente,
El equipo de PetHouse
"""
    return _send(user_email, subject, body)


def send_pet_approval_email(user_email: str, user_name: str, pet_name: str) -> bool:
    subject = f"¡Tu publicación de {pet_name} fue aprobada!"
    body = f"""Hola {user_name},

¡Buenas noticias! Tu publicación de {pet_name} ha sido APROBADA por nuestro equipo y ya es visible en el catálogo público de PetHouse. 🎉

Pronto recibirás solicitudes de adoptantes interesados.

Gracias por contribuir a darle un hogar a quien más lo necesita.

Atentamente,
El equipo de PetHouse
"""
    return _send(user_email, subject, body)


def send_pet_rejection_email(user_email: str, user_name: str, pet_name: str) -> bool:
    subject = f"Actualización sobre tu publicación de {pet_name}"
    body = f"""Hola {user_name},

Lamentamos informarte que tu publicación de {pet_name} no pudo ser aprobada.

Algunos motivos pueden ser: información incompleta, imágenes inadecuadas o incumplimiento de nuestras políticas de publicación.

Si deseas corregir la información y volver a intentarlo, inicia sesión en PetHouse y edita tu publicación.

Atentamente,
El equipo de PetHouse
"""
    return _send(user_email, subject, body)


def send_sede_instructions_email(user_email: str, user_name: str, pet_name: str) -> bool:
    subject = f"¡Tu publicación de {pet_name} fue aprobada! — Instrucciones de entrega en sede"
    body = f"""Hola {user_name},

¡Excelentes noticias! Tu publicación de {pet_name} ha sido APROBADA. 🎉

Como indicaste que deseas entregar a {pet_name} en nuestra sede, te compartimos los pasos a seguir:

PASOS A SEGUIR:
1. Acércate a nuestra sede en los próximos 5 días hábiles.
2. Trae tu documento de identidad original.
3. Trae a {pet_name} con correa o guacal según corresponda.
4. Si tienes cartilla de vacunación u otros documentos médicos, tráelos también (no obligatorio).

UBICACIÓN:
Casa PetHouse — Barranquilla, Colombia.
Dirección: Calle 72 #46-23, Barranquilla.

HORARIO DE ATENCIÓN:
Lunes a Viernes: 8:00 AM – 5:00 PM
Sábado: 9:00 AM – 1:00 PM

Una vez recibamos a {pet_name} en nuestra sede, quedará disponible en el catálogo y nuestro equipo estará a cargo de su cuidado hasta encontrarle un hogar.

Si tienes alguna duda o necesitas reprogramar, responde a este correo.

¡Gracias por ayudarnos a hacer la diferencia!

Atentamente,
El equipo de PetHouse
"""
    return _send(user_email, subject, body)


def send_adoption_request_email(user_email: str, user_name: str, pet_name: str) -> bool:
    subject = f"¡Solicitud de adopción recibida para {pet_name}!"
    body = f"""Hola {user_name},

Hemos recibido tu solicitud de adopción para {pet_name}. 🐾

Nuestro equipo revisará tu documentación y te notificará por correo electrónico en cuanto tengamos una respuesta.

¿QUÉ SIGUE?
1. Nuestro equipo revisará tu cédula y recibo de servicios.
2. Recibirás un correo con la decisión (aprobada o rechazada).
3. Si es aprobada, te indicaremos los pasos para recoger a {pet_name}.

Si tienes alguna duda, responde a este correo.

Gracias por considerar adoptar y darle un hogar a quien lo necesita.

Atentamente,
El equipo de PetHouse
"""
    return _send(user_email, subject, body)
