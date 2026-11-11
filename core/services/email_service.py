import logging

from core.tasks.email import send_email

from kombu.exceptions import OperationalError

logger = logging.getLogger(__name__)


class EmailService:
    """Sends templated emails in the background. Knows nothing about what the email is for."""

    @staticmethod
    def send(to: str, subject: str, template_name: str, context: dict) -> None:
        try:
            send_email.delay(to=to, subject=subject, template_name=template_name, context=context)
        except OperationalError:
            # broker is down: the request has already done its job (user saved etc.), so don't turn it into a 500;
            # the user can ask for the email again (verify-email/resend, password/reset)
            logger.exception('Could not queue email "%s" to %s', subject, to)
