import os

EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_USE_TLS = True


# transport layer security (TLS) is a cryptographic protocol that provides secure communication
# over a computer network. It is designed to prevent eavesdropping, tampering, and message forgery.
# TLS is widely used in applications such as web browsing, email, instant messaging, and voice over IP (VoIP).