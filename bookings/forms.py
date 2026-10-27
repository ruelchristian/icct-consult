import datetime
from django import forms
from django.utils import timezone
from .models import Booking
from directory.models import Category

INPUT_CLS = 'input input-bordered w-full bg-white text-slate-900 border-slate-300 placeholder-slate-400 focus:bg-white focus:text-slate-900 focus:border-icct-navy'
SELECT_CLS = 'select select-bordered w-full bg-white text-slate-900 border-slate-300 focus:bg-white focus:text-slate-900 focus:border-icct-navy'
TEXTAREA_CLS = 'textarea textarea-bordered w-full bg-white text-slate-900 border-slate-300 placeholder-slate-400 focus:bg-white focus:text-slate-900 focus:border-icct-navy'

class BookingCreateForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': INPUT_CLS,
            'hx-get': '', # Set dynamically in view
            'hx-target': '#available-slots-container',
            'hx-trigger': 'change',
        })
    )
    time_slot = forms.CharField(
        widget=forms.HiddenInput(),
        required=True,
        help_text="Selected start and end time (format: HH:MM-HH:MM)"
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': SELECT_CLS})
    )
    mode = forms.ChoiceField(
        choices=Booking.Mode.choices,
        widget=forms.Select(attrs={'class': SELECT_CLS})
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': TEXTAREA_CLS,
            'rows': 3,
            'placeholder': 'State your purpose or subject topic for this consultation (e.g. Capstone project defense inquiry, Midterm exam review)...'
        })
    )

    def clean_date(self):
        d = self.cleaned_data['date']
        today = timezone.localdate()
        if d < today:
            raise forms.ValidationError("You cannot book consultations in the past.")
        max_future = today + datetime.timedelta(days=14)
        if d > max_future:
            raise forms.ValidationError("Consultations can only be scheduled up to 2 weeks in advance.")
        return d

    def clean_time_slot(self):
        slot = self.cleaned_data['time_slot'].strip()
        if '-' not in slot:
            raise forms.ValidationError("Please select an available consultation slot.")
        return slot

class ActionReasonForm(forms.Form):
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': TEXTAREA_CLS,
            'rows': 2,
            'placeholder': 'Provide reason or remarks (optional)...'
        })
    )
