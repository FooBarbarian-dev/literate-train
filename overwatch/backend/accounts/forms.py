from django import forms
from django.core.exceptions import ValidationError
from accounts.validators import validate_username, validate_password_input
from rest_framework.exceptions import ValidationError as DRFValidationError

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        try:
            validate_username(username)
        except DRFValidationError as e:
            raise ValidationError("Invalid username format")
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            validate_password_input(password)
        except DRFValidationError as e:
            raise ValidationError("Invalid password format")
        return password
