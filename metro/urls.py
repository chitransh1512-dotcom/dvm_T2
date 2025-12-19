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

    path("profile/", views.edit_profile, name="edit_profile"),

    path("scan/offline-create/", views.offline_create_ticket, name="offline_create_ticket"),

    path("scanner/", views.scanner_dashboard, name="scanner_dashboard"),

    path("map/", views.metro_map_svg, name="metro_map"),

    path("api/shortest-route/", views.api_shortest_route, name="api_shortest_route"),
    
    path("api/route-by-ticket/", views.api_route_by_ticket, name="route_by_ticket"),



]
