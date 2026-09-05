import asyncio
from email.message import EmailMessage
import tracemalloc
from fastapi_mail import MessageSchema, FastMail
from pydantic import EmailStr
from starlette.responses import JSONResponse

from app.core.constants import FORGOT_PASSWORD_MAIL_SEND_SUCCESSFULLY
from app.core.settings.config import BaseConfig


async def send_mail(subject:str, message:str, recipient_list):
    """
    Handle the email sending process.
    """
    message = MessageSchema(
        subject=subject,
        recipients=recipient_list,
        body=message,
        subtype="plain"
    )

    mail = FastMail(BaseConfig.mail_conf)
    await mail.send_message(message)
    return JSONResponse(status_code=200, content={"message": FORGOT_PASSWORD_MAIL_SEND_SUCCESSFULLY})
