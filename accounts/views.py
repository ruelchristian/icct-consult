from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from directory.models import Department, StudentProfile, FacultyProfile
from .forms import LoginForm, StudentRegistrationForm, UserProfileForm

def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']

            # Lookup by username, school email, or school ID
            user = None
            try:
                user_obj = User.objects.filter(
                    username__iexact=username_or_email
                ).first() or User.objects.filter(
                    email__iexact=username_or_email
                ).first() or User.objects.filter(
                    school_id__iexact=username_or_email
                ).first()

                if user_obj and user_obj.check_password(password):
                    user = user_obj
            except Exception:
                user = None

            if user and user.is_active:
                login(request, user)
                messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
                next_url = request.GET.get('next') or 'core:home'
                return redirect(next_url)
            else:
                messages.error(request, "Invalid school credentials. Please check your Student/Employee ID or email.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('accounts:login')

def register_student_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user, profile = form.save()
            login(request, user)
            messages.success(request, f"Welcome to ICCT Consultations, {user.get_full_name()}! Your student account is active.")
            return redirect('core:home')
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile information has been updated.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'user': user,
    })
