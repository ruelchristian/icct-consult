from django import forms
from .models import AvailabilitySlot

INPUT_STYLE = 'background-color: #ffffff !important; color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; caret-color: #0a315a !important;'
INPUT_CLS = 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 placeholder-slate-400 focus:bg-white focus:text-slate-900 focus:border-[#0a315a] focus:ring-2 focus:ring-[#0a315a]/20 focus:outline-none transition text-base'
SELECT_CLS = 'w-full px-3 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 focus:bg-white focus:text-slate-900 focus:border-[#0a315a] focus:ring-2 focus:ring-[#0a315a]/20 focus:outline-none transition text-base'

DAY_PRESET_CHOICES = [
    ('', '- Select Day or Quick Preset -'),
    ('⚡ Quick Day Presets', [
        ('WEEKDAYS', 'All Weekdays (Monday to Friday)'),
        ('WEEKENDS', 'Full Weekend (Saturday & Sunday)'),
        ('ALL_DAYS', 'Every Day (Monday to Sunday)'),
    ]),
    ('📅 Individual Days', [
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ]),
]

class AvailabilitySlotForm(forms.ModelForm):
    day_of_week = forms.ChoiceField(
        choices=DAY_PRESET_CHOICES,
        widget=forms.Select(attrs={'class': SELECT_CLS, 'style': INPUT_STYLE, 'id': 'id_day_of_week'}),
        label="Day or Quick Preset"
    )

    class Meta:
        model = AvailabilitySlot
        fields = ['start_time', 'end_time', 'slot_duration_minutes', 'mode', 'location_or_link']
        widgets = {
            'start_time': forms.TimeInput(attrs={'class': INPUT_CLS, 'style': INPUT_STYLE, 'type': 'time', 'id': 'id_start_time'}),
            'end_time': forms.TimeInput(attrs={'class': INPUT_CLS, 'style': INPUT_STYLE, 'type': 'time', 'id': 'id_end_time'}),
            'slot_duration_minutes': forms.NumberInput(attrs={'class': INPUT_CLS, 'style': INPUT_STYLE, 'min': '15', 'step': '15', 'id': 'id_slot_duration'}),
            'mode': forms.Select(attrs={'class': SELECT_CLS, 'style': INPUT_STYLE, 'id': 'id_mode'}),
            'location_or_link': forms.TextInput(attrs={'class': INPUT_CLS, 'style': INPUT_STYLE, 'placeholder': 'e.g. CCS Faculty Room 302', 'id': 'id_location_or_link'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        mode = cleaned_data.get('mode')
        loc = (cleaned_data.get('location_or_link') or '').strip()

        if start and end and start >= end:
            self.add_error('end_time', "End time must be after start time.")

        # Require a valid meeting URL when Online (Virtual) is selected
        if mode == AvailabilitySlot.Mode.ONLINE:
            if not loc:
                self.add_error('location_or_link', "A virtual meeting link (e.g. Google Meet or Zoom URL) is required when Mode is Online.")
            elif not (loc.startswith('http://') or loc.startswith('https://')):
                self.add_error('location_or_link', "Please enter a valid URL starting with https:// or http:// (e.g. https://meet.google.com/abc-defg-hij).")

        return cleaned_data

    def save_slots(self, faculty):
        """
        Saves slots for an individual day or bulk creates across presets.
        """
        day_val = str(self.cleaned_data['day_of_week'])
        if day_val == 'WEEKDAYS':
            target_days = [0, 1, 2, 3, 4]
        elif day_val == 'WEEKENDS':
            target_days = [5, 6]
        elif day_val == 'ALL_DAYS':
            target_days = [0, 1, 2, 3, 4, 5, 6]
        else:
            target_days = [int(day_val)]

        slots = []
        for d in target_days:
            slot, _ = AvailabilitySlot.objects.update_or_create(
                faculty=faculty,
                day_of_week=d,
                start_time=self.cleaned_data['start_time'],
                end_time=self.cleaned_data['end_time'],
                defaults={
                    'slot_duration_minutes': self.cleaned_data['slot_duration_minutes'],
                    'mode': self.cleaned_data['mode'],
                    'location_or_link': self.cleaned_data['location_or_link'],
                    'is_active': True,
                }
            )
            slots.append(slot)
        return slots
