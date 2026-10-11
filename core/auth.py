"""Public account creation using Django's password and session protections."""
from django import forms
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods


class SignupForm(UserCreationForm):
    email = forms.EmailField(help_text="Used to identify your account.")

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account already uses this email. Please sign in.")
        return email


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect("assistant")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        # Django rotates the guest session and emits user_logged_in. Our
        # signal transfers only conversations owned by that previous session.
        login(request, user)
        return redirect("assistant")
    return render(request, "registration/signup.html", {"form": form, "page_title": "Create account"})
