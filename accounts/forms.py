from django import forms
from django.db import transaction
from .models import User
from directory.models import StudentProfile, Department

class LoginForm(forms.Form):
    username_or_email = forms.CharField(
        label="Student / Employee ID or Email",
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full bg-base-100',
            'placeholder': 'e.g. 2026-10123 or juandelacruz@icct.edu.ph',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full bg-base-100',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )

class StudentRegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Last Name'})
    )
    student_number = forms.CharField(
        max_length=30,
        label="Student ID Number",
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g. 2026-00123'})
    )
    email = forms.EmailField(
        label="School Email Address",
        widget=forms.EmailInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'student@icct.edu.ph'})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': '09123456789'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'})
    )
    program = forms.CharField(
        max_length=100,
        label="Degree Program / Course",
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g. BS Information Technology'})
    )
    year_level = forms.ChoiceField(
        choices=[(1, '1st Year'), (2, '2nd Year'), (3, '3rd Year'), (4, '4th Year')],
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'})
    )
    section = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g. BSIT-4A'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'At least 8 characters'})
    )
    password_confirm = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Confirm your password'})
    )

    def clean_student_number(self):
        sn = self.cleaned_data['student_number'].strip()
        if User.objects.filter(school_id__iexact=sn).exists() or StudentProfile.objects.filter(student_number__iexact=sn).exists():
            raise forms.ValidationError("This student number is already registered.")
        return sn

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password_confirm')
        if p1 and p2 and p1 != p2:
            self.add_error('password_confirm', "Passwords do not match.")
        return cleaned_data

    @transaction.atomic
    def save(self):
        data = self.cleaned_data
        username = data['student_number'].lower().replace('-', '').replace(' ', '')
        user = User.objects.create_user(
            username=username,
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            school_id=data['student_number'],
            phone_number=data.get('phone_number', ''),
            role=User.Role.STUDENT
        )

        student_profile = StudentProfile.objects.create(
            user=user,
            student_number=data['student_number'],
            department=data.get('department'),
            program=data['program'],
            year_level=int(data['year_level']),
            section=data.get('section', '')
        )
        return user, student_profile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'phone_number': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
        }
