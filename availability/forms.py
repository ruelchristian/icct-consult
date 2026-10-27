from django import forms
from .models import AvailabilitySlot

INPUT_STYLE = 'background-color: #ffffff !important; color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; caret-color: #0a315a !important;'
INPUT_CLS = 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 placeholder-slate-400 focus:bg-white focus:text-slate-900 focus:border-[#0a315a] focus:ring-2 focus:ring-[#0a315a]/20 focus:outline-none transition text-base'
SELECT_CLS = 'w-full px-3 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 focus:bg-white focus:text-slate-900 focus:border-[#0a315a] focus:ring-2 focus:ring-[#0a315a]/20 focus:outline-none transition text-base'

class AvailabilitySlotForm(forms.ModelForm):
    class Meta:
        model = AvailabilitySlot
        fields = ['day_of_week', 'start_time', 'end_time', 'slot_duration_minutes', 'mode', 'location_or_link']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': SELECT_CLS, 'style': INPUT_STYLE}),
            'start_time': forms.TimeInput(attrs={'class': INPUT_CLS, 'style': INPUT_STYLE, 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': INPUT_CLS, 'style': INPUT_STYLE, 'type': 'time'}),
            'slot_duration_minutes': forms.NumberInput(attrs={'class': INPUT_CLS, 'style': INPUT_STYLE, 'min': '15', 'step': '15'}),
            'mode': forms.Select(attrs={'class': SELECT_CLS, 'style': INPUT_STYLE}),
            'location_or_link': forms.TextInput(attrs={'class': INPUT_CLS, 'style': INPUT_STYLE, 'placeholder': 'e.g. Room 302 or Google Meet link'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and start >= end:
            self.add_error('end_time', "End time must be after start time.")
        return cleaned_data
