from django.shortcuts import render
from decimal import Decimal

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from .models import Station, Ticket, Profile, Footfall,MetroService
from .forms import BuyTicketForm, AddMoneyForm, OTPForm, UserProfileForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Line,LineStation
from django.contrib.auth.decorators import user_passes_test
from .graph import shortest_distance,shortest_path
from allauth.account.models import EmailAddress
from .otp import send_otp


import uuid
from .otp import  validate_otp
from .utils import notify_ticket_purchase
from .graph import shortest_distance

BASE_FARE_PER_STATION = 5

def is_scanner(user):
    return user.groups.filter(name="Scanner").exists()

def index(request):
    return render(request, "metro/index.html")

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

    if not metro_service_active():
        messages.error(request, "Metro services are currently not running.")
        return redirect("metro:buy_ticket")
    
    # Check global metro service
    if not metro_service_active():
        messages.error(request, "Metro services are currently not running.")
        return redirect("metro:buy_ticket")

    if from_station == to_station:
        messages.error(request, "Please choose two different stations.")
        return redirect("metro:buy_ticket")

    try:
        distance = shortest_distance(from_station, to_station)
    except:
        # fallback for phase 1
        distance = abs(from_station.order - to_station.order)

    # Validate all lines used in the computed route
    try:
        path = shortest_path(from_station, to_station)
    except:
        messages.error(request, "No valid route found.")
        return redirect("metro:buy_ticket")

    path_station_ids = [s.id for s in path]

    used_line_ids = (
        LineStation.objects
        .filter(station_id__in=path_station_ids)
        .values_list("line_id", flat=True)
        .distinct()
    )

    if Line.objects.filter(id__in=used_line_ids, active=False).exists():
        messages.error(
            request,
            "Ticket purchase is disabled due to inactive metro line on this route."
        )
        return redirect("metro:buy_ticket")


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


    #  OTP generation
    send_otp(request.user)
    messages.info(request, "OTP sent to your email.")
    return redirect("metro:verify_otp")

@login_required
def verify_otp(request):
    pending = request.session.get("pending_purchase")
    if not pending:
        return redirect("metro:buy_ticket")

    form = OTPForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        otp = form.cleaned_data["otp"]

        email = (
            EmailAddress.objects
            .filter(user=request.user, verified=True)
            .order_by("-primary")
            .values_list("email", flat=True)
            .first()
        )

        if not email or not validate_otp(email, otp):
            messages.error(request, "Invalid or expired OTP.")
            return redirect("metro:verify_otp")

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

        notify_ticket_purchase(request.user, ticket)
        del request.session["pending_purchase"]

        messages.success(request, f"Ticket created: {ticket.ticket_code}")
        return redirect("metro:my_tickets")

    return render(request, "metro/verify_otp.html", {"form": form})


@login_required
def my_tickets(request):
    tickets = request.user.tickets.all().order_by("-created_at")
    for t in tickets:
        t.auto_expire_if_needed()
    return render(request, "metro/my_tickets.html", {"tickets": tickets})


from django.http import JsonResponse

@login_required
def api_shortest_route(request):
    from_id = request.GET.get("from")
    to_id = request.GET.get("to")

    if not from_id or not to_id:
        return JsonResponse({"ok": False, "error": "Missing params"})

    try:
        from_station = Station.objects.get(id=from_id)
        to_station = Station.objects.get(id=to_id)
    except Station.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Invalid station"})

    # BFS
    try:
        path = shortest_path(from_station, to_station)

    except:
        return JsonResponse({"ok": False, "error": "No route found"})
    
    coord_map = {
        st.id: (st.x, st.y)
        for st in Station.objects.all()
    }


    points = []
    for station in path:
        x, y = coord_map[station.id]
        points.append({"x": x, "y": y})

    hops = len(path) - 1
    price = hops * BASE_FARE_PER_STATION

    return JsonResponse({
        "ok": True,
        "route": [s.name for s in path],
        "distance": hops,
        "price": price,
        "points": points
})


@login_required
def api_route_by_ticket(request):
    ticket_code = request.GET.get("ticket")

    if not ticket_code:
        return JsonResponse({"ok": False, "error": "Missing ticket code"})

    try:
        ticket = Ticket.objects.get(ticket_code=ticket_code, owner=request.user)
    except Ticket.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Invalid ticket"})

    try:
        path = shortest_path(ticket.from_station, ticket.to_station)
    except:
        return JsonResponse({"ok": False, "error": "No route found"})

    points = [{"x": st.x, "y": st.y} for st in path]

    return JsonResponse({
        "ok": True,
        "route": [st.name for st in path],
        "points": points
    })


from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
@login_required
@user_passes_test(is_scanner)
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


    ticket.auto_expire_if_needed()

    if ticket.status == "EXPIRED":
        return JsonResponse({"ok": False, "error": "Ticket expired"}, status=400)

    if action == "in":
        if ticket.status != "ACTIVE":
            return JsonResponse({"ok": False, "error": "Ticket not ACTIVE"}, status=400)

        ticket.mark_inuse()
        increment_footfall(ticket.from_station)
        return JsonResponse({"ok": True, "status": "INUSE"})


    elif action == "out":
        if ticket.status != "INUSE":
            return JsonResponse({"ok": False, "error": "Ticket not INUSE"}, status=400)
        ticket.mark_used()
        increment_footfall(ticket.to_station)
        return JsonResponse({"ok": True, "status": "USED"})

    return JsonResponse({"ok": False, "error": "Unknown action"}, status=400)

@login_required
def edit_profile(request):
    """
    Allow logged-in users to edit their basic profile details
    (username, first name, last name, email).
    """
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("metro:edit_profile")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "metro/edit_profile.html", {"form": form})

@csrf_exempt
@require_POST
@login_required
@user_passes_test(is_scanner)
def offline_create_ticket(request):
    """
    Create a ticket offline at station and mark it as USED immediately.
    {
        "from_station": 1,
        "to_station": 3,
        "price": 20,
        "operator_key": "scanner123"
    }
    """
    import json
    data = json.loads(request.body.decode("utf-8"))

    

    # Extract fields
    from_id = data.get("from_station")
    to_id = data.get("to_station")
    price = data.get("price")

    if not from_id or not to_id or not price:
        return JsonResponse({"ok": False, "error": "Missing fields"}, status=400)

    try:
        from_station = Station.objects.get(id=from_id)
        to_station = Station.objects.get(id=to_id)
    except Station.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Invalid station"}, status=404)

    # Creating ticket with no owner (offline)
    ticket = Ticket.objects.create(
        owner=None,
        from_station=from_station,
        to_station=to_station,
        price=price,
        ticket_code=uuid.uuid4().hex[:12],
        status="USED",  # Mark immediately used
    )

    return JsonResponse({
        "ok": True,
        "ticket_code": ticket.ticket_code,
        "status": "USED"
    })

def increment_footfall(station):
    today = timezone.now().date()
    ff, created = Footfall.objects.get_or_create(
        station=station,
        date=today,
        defaults={"count": 0}
    )
    ff.count += 1
    ff.save()

def metro_service_active():
    svc = MetroService.objects.first()
    return True if svc is None else svc.is_running

@login_required
@user_passes_test(is_scanner)
def scanner_dashboard(request):
    return render(request, "metro/scanner_dashboard.html")

@login_required
def metro_map_svg(request):
    from collections import Counter

    lines = Line.objects.filter(active=True).order_by("id")
    line_data = []

    # Detect interchanges (stations in more than one line) 
    station_ids = []
    for line in lines:
        station_ids += list(
            LineStation.objects.filter(line=line)
            .values_list("station_id", flat=True)
        )

    counts = Counter(station_ids)
    interchanges = {sid for sid, c in counts.items() if c > 1}

    # Build SVG data per line 
    for line in lines:
        ls = (
            LineStation.objects
            .filter(line=line)
            .select_related("station")
            .order_by("position")
        )

        stations = [s.station for s in ls]

        for st in stations:
            st.label_x = st.x + 10
            st.label_y = st.y - 10

        # Build polyline using real coordinates
        points = " ".join(f"{st.x},{st.y}" for st in stations)

        line_data.append({
            "line": line,
            "stations": stations,
            "points": points,
        })

    return render(
        request,
        "metro/metro_map_svg.html",
        {
            "line_data": line_data,
            "interchanges": interchanges,
        }
    )
