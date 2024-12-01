# app/utils/email.py
import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pathlib import Path
from app.config import settings
from jinja2 import Template

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=587,
    MAIL_FROM_NAME="CV Builder Pro",
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    VALIDATE_CERTS=False, #To be removed after Testing
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / 'templates' / 'email'
)

async def send_verification_email_(email: str, token: str, subject: str, template: str, data: dict):
    """Send verification email with custom template"""
    logging.info(f"Sending email to {email}")
    logging.info(f"Token: {token}")

    # Create the verification URL using the token
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    # Load the template (assuming you're using Jinja2 or a similar templating engine)
    template_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #0070f3; padding: 20px; text-align: center; }
            .header h1 { color: white; margin: 0; }
            .content { padding: 30px 20px; background-color: #fff; }
            .button {
                background-color: #0070f3;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 5px;
                display: inline-block;
                margin: 20px 0;
            }
            .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>CV Builder Pro</h1>
            </div>
            <div class="content">
                <h2>Welcome!</h2>
                <p>Thank you for choosing CV Builder Pro. Please verify your email to get started.</p>
                <div style="text-align: center;">
                    <a href="{{ verify_url }}" class="button">Verify Email Address</a>
                </div>
                <p><strong>Or copy this link:</strong><br>
                {{ verify_url }}</p>
                <p><small>Link expires in 48 hours</small></p>
            </div>
            <div class="footer">
                <p>CV Builder Pro • Professional CV Creation</p>
                <p>If you didn't create an account, please ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
"""


# Set sender name in email configuration

    # Create a Jinja2 template object
    template_obj = Template(template_content)
    
    # Render the template with the provided data
    html = template_obj.render(verify_url=verification_url, expires_in="48 hours")

    # Create the email message
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    # Send the email using FastMail
    fm = FastMail(conf)
    await fm.send_message(message)