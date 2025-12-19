from django import forms
from .models import Station
from django.contrib.auth.models import User  

class BuyTicketForm(forms.Form):
    from_station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        label="From",
    )
    to_station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        label="To",
    )

class AddMoneyForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=1,
        label="Amount",
    )


class OTPForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        label="Enter OTP",
        widget=forms.TextInput(attrs={"placeholder": "6-digit code"})
    )

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        labels = {
            "username": "Username",
            "first_name": "First name",
            "last_name": "Last name",
            "email": "Email address",
        }