from django import forms
from .models import AvailabilitySlot

INPUT_CLS = 'input input-bordered w-full bg-white text-slate-900 border-slate-300 placeholder-slate-400 focus:bg-white focus:text-slate-900 focus:border-icct-navy'
SELECT_CLS = 'select select-bordered w-full bg-white text-slate-900 border-slate-300 focus:bg-white focus:text-slate-900 focus:border-icct-navy'

class AvailabilitySlotForm(forms.ModelForm):
    class Meta:
        model = AvailabilitySlot
        fields = ['day_of_week', 'start_time', 'end_time', 'slot_duration_minutes', 'mode', 'location_or_link']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': SELECT_CLS}),
            'start_time': forms.TimeInput(attrs={'class': INPUT_CLS, 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': INPUT_CLS, 'type': 'time'}),
            'slot_duration_minutes': forms.NumberInput(attrs={'class': INPUT_CLS, 'min': '15', 'step': '15'}),
            'mode': forms.Select(attrs={'class': SELECT_CLS}),
            'location_or_link': forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': 'e.g. Room 302 or Google Meet link'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and start >= end:
            self.add_error('end_time', "End time must be after start time.")
        return cleaned_data
