from django import forms
from .models import SessionRecord

SELECT_CLS = 'select select-bordered w-full bg-white text-slate-900 border-slate-300 focus:bg-white focus:text-slate-900 focus:border-icct-navy'
TEXTAREA_CLS = 'textarea textarea-bordered w-full bg-white text-slate-900 border-slate-300 placeholder-slate-400 focus:bg-white focus:text-slate-900 focus:border-icct-navy'

class SessionRecordForm(forms.ModelForm):
    class Meta:
        model = SessionRecord
        fields = ['attendance', 'advice_given', 'action_items', 'private_notes']
        widgets = {
            'attendance': forms.Select(attrs={'class': SELECT_CLS}),
            'advice_given': forms.Textarea(attrs={
                'class': TEXTAREA_CLS,
                'rows': 4,
                'placeholder': 'Key guidance, explanations, recommendations, or feedback for the student (visible to student)...'
            }),
            'action_items': forms.Textarea(attrs={
                'class': TEXTAREA_CLS,
                'rows': 3,
                'placeholder': 'Deliverables, revisions, or tasks student should complete (visible to student)...'
            }),
            'private_notes': forms.Textarea(attrs={
                'class': TEXTAREA_CLS,
                'rows': 3,
                'placeholder': 'Internal faculty notes, grading observations, or confidential remarks (NOT visible to student)...'
            }),
        }
