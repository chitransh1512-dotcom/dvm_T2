from django.core.mail import send_mail


def notify_ticket_purchase(user, ticket):
    """
    Sends a simple email to user after successful ticket purchase.
    """
    subject = "Metro Ticket Confirmation"
    message = (
        f"Hello {user.username},\n\n"
        f"Your metro ticket has been issued.\n"
        f"Ticket Code: {ticket.ticket_code}\n"
        f"From: {ticket.from_station.name}\n"
        f"To: {ticket.to_station.name}\n"
        f"Price: ₹{ticket.price}\n\n"
        "Thank you for using Metro Services."
    )

    send_mail(
        subject,
        message,
        None,               # Uses DEFAULT_FROM_EMAIL from settings
        [user.email],
        fail_silently=True  # Keeps it simple for beginners
    )
