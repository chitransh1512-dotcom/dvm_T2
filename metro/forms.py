from django import forms
from .models import Station


# -----------------------------
#  Buy Ticket Form
# -----------------------------
class BuyTicketForm(forms.Form):
    from_station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        label="From",
    )
    to_station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        label="To",
    )


# -----------------------------
#  Add Money to Wallet
# -----------------------------
class AddMoneyForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=1,
        label="Amount",
    )


# -----------------------------
#  OTP Form (Phase 2)
# -----------------------------
class OTPForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        label="Enter OTP",
        widget=forms.TextInput(attrs={"placeholder": "6-digit code"})
    )
