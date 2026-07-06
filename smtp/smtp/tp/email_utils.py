from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def send_smtp_email(subject, body, to, from_email=None, html=None, fail_silently=False):
    """Send an email using Django's SMTP backend.

    - `to` can be a single email or an iterable of emails.
    - `html` optional HTML alternative body.
    """
    if isinstance(to, str):
        recipients = [to]
    else:
        recipients = list(to)

    from_email = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None)
    msg = EmailMultiAlternatives(subject, body, from_email, recipients)
    if html:
        msg.attach_alternative(html, "text/html")
    return msg.send(fail_silently=fail_silently)
