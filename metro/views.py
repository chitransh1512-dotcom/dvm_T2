from django.shortcuts import render
from decimal import Decimal

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from .models import Station, Ticket, Profile
from .forms import BuyTicketForm, AddMoneyForm, OTPForm

import uuid

# Phase 2 helpers
from .otp import generate_otp, validate_otp
from .utils import notify_ticket_purchase

# If shortest path is used (Phase 2 multi-line)
from .graph import shortest_distance

BASE_FARE_PER_STATION = 5


# ---------------------------------------------------------
# Home
# ---------------------------------------------------------
def index(request):
    return render(request, "metro/index.html")


# ---------------------------------------------------------
# Add Money to Wallet
# ---------------------------------------------------------
@login_required
def add_money(request):
    form = AddMoneyForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        amount = form.cleaned_data["amount"]
        profile = Profile.objects.get(user=request.user)

        profile.wallet += amount
        profile.save()

        messages.success(request, f"₹{amount} added to your wallet.")
        return redirect("metro:buy_ticket")

    return render(request, "metro/add_money.html", {"form": form})


# ---------------------------------------------------------
# Buy Ticket (Phase 1 + Phase 2 OTP system)
# Step 1: Select stations
# Step 2: Generate OTP
# Step 3: Verify OTP → create ticket
# ---------------------------------------------------------
@login_required
def buy_ticket(request):
    # STEP 1: Choose from / to stations
    if request.method == "GET":
        form = BuyTicketForm()
        return render(request, "metro/buy_ticket.html", {"form": form})

    # STEP 2: User submitted form
    form = BuyTicketForm(request.POST)
    if not form.is_valid():
        return render(request, "metro/buy_ticket.html", {"form": form})

    from_station = form.cleaned_data["from_station"]
    to_station = form.cleaned_data["to_station"]

    if from_station == to_station:
        messages.error(request, "Please choose two different stations.")
        return redirect("metro:buy_ticket")

    # PHASE 1 – simple fare using order
    # PHASE 2 – shortest path using graph BFS
    try:
        distance = shortest_distance(from_station, to_station)
    except:
        # fallback for phase 1
        distance = abs(from_station.order - to_station.order)

    price = distance * BASE_FARE_PER_STATION

    profile = Profile.objects.get(user=request.user)
    if profile.wallet < price:
        messages.error(request, "Not enough balance. Add money first.")
        return redirect("metro:add_money")

    # Store pending purchase details in session
    request.session["pending_purchase"] = {
        "from_id": from_station.id,
        "to_id": to_station.id,
        "price": str(price),
    }

    # STEP 3: OTP generation
    otp = generate_otp(request.user.email)
    messages.info(request, "OTP sent to your email.")

    return redirect("metro:verify_otp")


# ---------------------------------------------------------
# Verify OTP and finalize purchase
# ---------------------------------------------------------
@login_required
def verify_otp(request):
    pending = request.session.get("pending_purchase")
    if not pending:
        return redirect("metro:buy_ticket")

    form = OTPForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        otp = form.cleaned_data["otp"]

        if not validate_otp(request.user.email, otp):
            messages.error(request, "Invalid or expired OTP.")
            return redirect("metro:verify_otp")

        # OTP success → create ticket
        from_station = Station.objects.get(id=pending["from_id"])
        to_station = Station.objects.get(id=pending["to_id"])
        price = Decimal(pending["price"])

        profile = Profile.objects.get(user=request.user)
        profile.wallet -= price
        profile.save()

        ticket = Ticket.objects.create(
            owner=request.user,
            from_station=from_station,
            to_station=to_station,
            price=price,
            ticket_code=uuid.uuid4().hex[:12],
        )

        # Email notification
        notify_ticket_purchase(request.user, ticket)

        del request.session["pending_purchase"]

        messages.success(request, f"Ticket created: {ticket.ticket_code}")
        return redirect("metro:my_tickets")

    return render(request, "metro/verify_otp.html", {"form": form})


# ---------------------------------------------------------
# Show user tickets
# ---------------------------------------------------------
@login_required
def my_tickets(request):
    tickets = request.user.tickets.all().order_by("-created_at")
    return render(request, "metro/my_tickets.html", {"tickets": tickets})


# ---------------------------------------------------------
# Ticket scanning (Phase 1)
# scanner devices hit this endpoint
# ---------------------------------------------------------
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def scan_ticket(request):
    """
    Request JSON:
    { "ticket_code": "ABC123", "action": "in" or "out" }
    """
    import json
    data = json.loads(request.body.decode("utf-8"))

    code = data.get("ticket_code")
    action = data.get("action")

    if not code:
        return JsonResponse({"ok": False, "error": "No ticket code"}, status=400)

    try:
        ticket = Ticket.objects.get(ticket_code=code)
    except Ticket.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Ticket not found"}, status=404)

    if action == "in":
        if ticket.status != "ACTIVE":
            return JsonResponse({"ok": False, "error": "Ticket not ACTIVE"}, status=400)
        ticket.mark_inuse()
        return JsonResponse({"ok": True, "status": "INUSE"})

    elif action == "out":
        if ticket.status != "INUSE":
            return JsonResponse({"ok": False, "error": "Ticket not INUSE"}, status=400)
        ticket.mark_used()
        return JsonResponse({"ok": True, "status": "USED"})

    return JsonResponse({"ok": False, "error": "Unknown action"}, status=400)
