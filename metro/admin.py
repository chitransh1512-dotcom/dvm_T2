from django.contrib import admin
from .models import (
    Station,
    Line,
    LineStation,
    Connection,
    Ticket,
    Profile
)
from .models import Footfall,MetroService

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "order","x","y")
    ordering = ("order",)
    search_fields = ("name",)
    list_editable = ("x", "y")


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "active")
    list_editable = ("active",)
    search_fields = ("name",)


@admin.register(LineStation)
class LineStationAdmin(admin.ModelAdmin):
    list_display = ("id", "line", "station", "position")
    list_filter = ("line",)
    ordering = ("line", "position")


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ("id", "a", "b")
    list_filter = ("a", "b")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_code",
        "owner",
        "from_station",
        "to_station",
        "price",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("ticket_code", "owner__username")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "wallet")
    search_fields = ("user__username",)

@admin.register(Footfall)
class FootfallAdmin(admin.ModelAdmin):
    list_display = ("station", "date", "count")
    list_filter = ("station", "date")

@admin.register(MetroService)
class MetroServiceAdmin(admin.ModelAdmin):
    list_display = ("is_running",)