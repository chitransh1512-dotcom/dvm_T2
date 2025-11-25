from django.urls import path
from . import views

app_name = "metro"

urlpatterns = [
    path("", views.index, name="index"),

    # Wallet
    path("add-money/", views.add_money, name="add_money"),

    # Ticket purchase flow
    path("buy/", views.buy_ticket, name="buy_ticket"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),

    # User tickets
    path("tickets/", views.my_tickets, name="my_tickets"),

    # Ticket scanner (API)
    path("scan/", views.scan_ticket, name="scan_ticket"),
]
