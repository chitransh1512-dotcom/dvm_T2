
# from django.db import models
# from django.contrib.auth.models import User

# # Create your models here.
# from django.db import models

# class Line(models.Model):
#     name = models.CharField(max_length=20)

#     def __str__(self):
#         return self.name


# class Station(models.Model):
#     name = models.CharField(max_length=50)
#     line = models.ForeignKey(Line, on_delete=models.CASCADE)
#     order = models.PositiveIntegerField()

#     def __str__(self):
#         return self.name


# class Ticket(models.Model):
#     customer_name = models.CharField(max_length=50)
#     customer_age = models.PositiveIntegerField()
#     customer_gender = models.CharField(max_length=10)

#     source = models.ForeignKey(
#         Station, on_delete=models.CASCADE, related_name="source_tickets"
#     )
#     destination = models.ForeignKey(
#         Station, on_delete=models.CASCADE, related_name="destination_tickets"
#     )

#     fare = models.PositiveIntegerField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Ticket {self.id}"
    
# class LineStation(models.Model):
#     line = models.ForeignKey(Line, on_delete=models.CASCADE, related_name="line_stations")
#     station = models.ForeignKey(Station, on_delete=models.CASCADE)
#     position = models.PositiveIntegerField()

#     class Meta:
#         ordering = ["line", "position"]
#         unique_together = ("line", "station")

# class Connection(models.Model):
#     a = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="conn_a")
#     b = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="conn_b")

#     def __str__(self):
#         return f"{self.a} <-> {self.b}"

# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     wallet = models.DecimalField(max_digits=8, decimal_places=2, default=0)

#     def __str__(self):
#         return self.user.username
from django.db import models
from django.contrib.auth.models import User


# -----------------------------
#  Station Model
# -----------------------------
class Station(models.Model):
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


# -----------------------------
#  Line Model
# -----------------------------
class Line(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# -----------------------------
#  LineStation (Station ordering inside a Line)
# -----------------------------
class LineStation(models.Model):
    line = models.ForeignKey(Line, on_delete=models.CASCADE, related_name="line_stations")
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["line", "position"]
        unique_together = ("line", "station")

    def __str__(self):
        return f"{self.line.name} - {self.station.name}"


# -----------------------------
#  Connection (for shortest path)
# -----------------------------
class Connection(models.Model):
    a = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="conn_a")
    b = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="conn_b")

    def __str__(self):
        return f"{self.a} <-> {self.b}"


# -----------------------------
#  Profile (Wallet system)
# -----------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wallet = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return self.user.username


# -----------------------------
#  Ticket Model
# -----------------------------
TICKET_STATUS = [
    ("ACTIVE", "Active"),
    ("INUSE", "In Use"),
    ("USED", "Used"),
    ("EXPIRED", "Expired"),
]


class Ticket(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    from_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="tickets_from")
    to_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="tickets_to")
    price = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=TICKET_STATUS, default="ACTIVE")
    ticket_code = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return f"Ticket {self.ticket_code}"

    def mark_used(self):
        self.status = "USED"
        self.save()

    def mark_inuse(self):
        self.status = "INUSE"
        self.save()
