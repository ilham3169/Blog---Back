import aiosmtplib
from email.message import EmailMessage
from dotenv import dotenv_values

env = dotenv_values(".env")

SMTP_HOST = env["SMTP_HOST"]
SMTP_PORT = int(env["SMTP_PORT"])
SMTP_USER = env["SMTP_USER"]
SMTP_PASSWORD = env["SMTP_PASSWORD"]
SMTP_FROM = env["SMTP_FROM"]

async def send_welcome_email(to_email: str, username: str):
    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = "Welcome to our system"
    msg.set_content(
        f"Hello {username},\n\nWelcome to our system! We are happy to have you.\n\nRegards,\nTeam"
    )

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=int(SMTP_PORT),
        start_tls=True,        
        username=SMTP_USER,
        password=SMTP_PASSWORD,
    )


async def send_login_message(to_email: str, username: str):
    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = "Logging In"
    msg.set_content(
        f"Hello {username},\n\nYou have successfully logged in.\n\nRegards,\nTeam"
    )

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=int(SMTP_PORT),
        start_tls=True,        
        username=SMTP_USER,
        password=SMTP_PASSWORD,
    )
    