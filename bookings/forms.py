import datetime
from django import forms
from django.utils import timezone
from .models import Booking
from directory.models import Category

INPUT_STYLE = 'background-color: #ffffff !important; color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; caret-color: #0a315a !important;'
INPUT_CLS = 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 placeholder-slate-400 focus:bg-white focus:text-slate-900 focus:border-[#0a315a] focus:ring-2 focus:ring-[#0a315a]/20 focus:outline-none transition text-base'
SELECT_CLS = 'w-full px-3 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 focus:bg-white focus:text-slate-900 focus:border-[#0a315a] focus:ring-2 focus:ring-[#0a315a]/20 focus:outline-none transition text-base'
TEXTAREA_CLS = 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 placeholder-slate-400 focus:bg-white focus:text-slate-900 focus:border-[#0a315a] focus:ring-2 focus:ring-[#0a315a]/20 focus:outline-none transition text-base'

class BookingCreateForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': INPUT_CLS,
            'style': INPUT_STYLE,
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
        widget=forms.Select(attrs={'class': SELECT_CLS, 'style': INPUT_STYLE})
    )
    mode = forms.ChoiceField(
        choices=Booking.Mode.choices,
        widget=forms.Select(attrs={'class': SELECT_CLS, 'style': INPUT_STYLE})
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': TEXTAREA_CLS,
            'style': INPUT_STYLE,
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
            'style': INPUT_STYLE,
            'rows': 2,
            'placeholder': 'Provide reason or remarks (optional)...'
        })
    )
