from django.core.management.base import BaseCommand
from tp.email_utils import send_smtp_email


class Command(BaseCommand):
    help = "Send a test email via configured SMTP settings"

    def add_arguments(self, parser):
        parser.add_argument('--to', nargs='+', required=True, help='Recipient email(s)')
        parser.add_argument('--subject', default='Django SMTP test', help='Email subject')
        parser.add_argument('--body', default='This is a test email sent from Django.', help='Plain text body')

    def handle(self, *args, **options):
        to = options['to']
        subject = options['subject']
        body = options['body']
        sent = send_smtp_email(subject, body, to)
        if sent:
            self.stdout.write(self.style.SUCCESS(f"Sent {sent} message(s) to {to}"))
        else:
            self.stdout.write(self.style.WARNING("No messages sent (check SMTP settings)."))
