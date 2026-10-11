from django import forms
from .models import AvailabilitySlot

class AvailabilitySlotForm(forms.ModelForm):
    class Meta:
        model = AvailabilitySlot
        fields = ['day_of_week', 'start_time', 'end_time', 'slot_duration_minutes', 'mode', 'location_or_link']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'start_time': forms.TimeInput(attrs={'class': 'input input-bordered w-full', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'input input-bordered w-full', 'type': 'time'}),
            'slot_duration_minutes': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'min': '15', 'step': '15'}),
            'mode': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'location_or_link': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g. Room 302 or Google Meet link'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and start >= end:
            self.add_error('end_time', "End time must be after start time.")
        return cleaned_data
