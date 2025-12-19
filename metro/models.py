from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Station(models.Model):
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField()
    x = models.IntegerField()
    y = models.IntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Line(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class LineStation(models.Model):
    line = models.ForeignKey(
        Line,
        on_delete=models.CASCADE,
        related_name="line_stations"
    )
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["line", "position"]
        unique_together = ("line", "station")

    def __str__(self):
        return f"{self.line.name} - {self.station.name}"


class Connection(models.Model):
    a = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="conn_a"
    )
    b = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="conn_b"
    )

    def __str__(self):
        return f"{self.a} <-> {self.b}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wallet = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return self.user.username


TICKET_STATUS = [
    ("ACTIVE", "Active"),
    ("INUSE", "In Use"),
    ("USED", "Used"),
    ("EXPIRED", "Expired"),
]

TICKET_VALIDITY_HOURS = 24   


class Ticket(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="tickets",
        null=True,
        blank=True          # allows offline tickets
    )

    from_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="tickets_from"
    )
    to_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="tickets_to"
    )

    price = models.DecimalField(max_digits=6, decimal_places=2)
    ticket_code = models.CharField(max_length=32, unique=True)

    status = models.CharField(
        max_length=10,
        choices=TICKET_STATUS,
        default="ACTIVE"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        expiry_time = self.created_at + timedelta(hours=TICKET_VALIDITY_HOURS)
        return timezone.now() >= expiry_time

    def auto_expire_if_needed(self):
        if self.status == "ACTIVE" and self.is_expired():
            self.status = "EXPIRED"
            self.save(update_fields=["status"])

    def mark_inuse(self):
        if self.status == "ACTIVE":
            self.status = "INUSE"
            self.save(update_fields=["status"])

    def mark_used(self):
        if self.status == "INUSE":
            self.status = "USED"
            self.save(update_fields=["status"])

    def __str__(self):
        return f"Ticket {self.ticket_code} ({self.status})"


class Footfall(models.Model):
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="footfall"
    )
    date = models.DateField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("station", "date")

    def __str__(self):
        return f"{self.station.name} - {self.date} : {self.count}"


class MetroService(models.Model):
    is_running = models.BooleanField(default=True)

    def __str__(self):
        return "Metro Service: ON" if self.is_running else "Metro Service: OFF"
