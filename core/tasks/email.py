from html import unescape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from config.celery import app


@app.task
def send_email(to: str, subject: str, template_name: str, context: dict) -> None:
    html_content = render_to_string(template_name, context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=unescape(strip_tags(html_content)),  # plain-text part: '&amp;' -> '&' in links
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
