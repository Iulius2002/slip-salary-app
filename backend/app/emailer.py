import smtplib
from email.message import EmailMessage
from typing import Iterable

def send_email(
    *,
    smtp_host: str,
    smtp_port: int,
    subject: str,
    sender: str,
    recipients: Iterable[str],
    body: str,
    attachments: list[tuple[str, bytes, str]] | None = None,  # (filename, content, mimetype)
):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    for (fname, content, mimetype) in (attachments or []):
        maintype, _, subtype = mimetype.partition("/")
        msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=fname)

    with smtplib.SMTP(host=smtp_host, port=smtp_port) as smtp:
        smtp.send_message(msg)
