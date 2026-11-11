from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend


class ReadableConsoleEmailBackend(ConsoleEmailBackend):
    """
    Local development only. Django's console backend prints the raw encoded message
    (quoted-printable: '=3D' instead of '=', broken lines), so links are hard to copy.
    This one prints just the headers and the plain-text body as-is.
    """

    def write_message(self, message):
        self.stream.write(
            f'From: {message.from_email}\n'
            f'To: {", ".join(message.to)}\n'
            f'Subject: {message.subject}\n\n'
            f'{message.body}\n'
        )
        self.stream.write('-' * 79 + '\n')
