from django import forms
from .models import VoterProfile
import re  # check password rule

class RegisterForm(forms.ModelForm):
    class Meta:
        model = VoterProfile
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'username', 'password']
        widgets = {
            'password': forms.PasswordInput(attrs={'placeholder': 'Strong Password (Min 8 chars)'}),
            'username': forms.TextInput(attrs={'placeholder': 'No spaces allowed'}),
        }

    # 1.. (Username Validation)
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        if len(username) < 4:
            raise forms.ValidationError("❌ Username must be at least 4 characters long.")
        if " " in username:
            raise forms.ValidationError("❌ Username cannot contain spaces.")
        if not username.isalnum():
            raise forms.ValidationError("❌ Username can only contain letters and numbers.")
            
        return username

    # 2.. (Password Validation)
    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        if len(password) < 8:
            raise forms.ValidationError("❌ Password must be at least 8 characters long.")
        if not re.search(r'\d', password):
            raise forms.ValidationError("❌ Password must contain at least one number (0-9).")
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("❌ Password must contain at least one Capital letter (A-Z).")
        if not re.search(r'[!@#$%^&*]', password):
            raise forms.ValidationError("❌ Password must contain at least one special character (!@#$%^&*).")
            
        return password