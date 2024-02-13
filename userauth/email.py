from django.core.mail import send_mail
from django.core.mail import EmailMessage
import random
from django.template.loader import render_to_string
from django.conf import settings
from .models import User


def send_otp(email,html,subject):
    # subject = "Account One Time Pin Verification!"
    otp = random.randint(100000,999999)
    message = render_to_string([html], {'otp':otp})
    email_from = settings.EMAIL_HOST
    # send_mail(subject, message,email_from, [email])
    email_message = EmailMessage(subject, message, email_from, [email])
    email_message.content_subtype = "html"  # Set the content type to HTML
    
    # Send the email
    email_message.send()
    user_otp = User.objects.get(email = email)
    user_otp.otp = otp
    user_otp.save()