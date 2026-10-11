from django import forms
from .models import SessionRecord

class SessionRecordForm(forms.ModelForm):
    class Meta:
        model = SessionRecord
        fields = ['attendance', 'advice_given', 'action_items', 'private_notes']
        widgets = {
            'attendance': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'advice_given': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Key guidance, explanations, recommendations, or feedback for the student (visible to student)...'
            }),
            'action_items': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Deliverables, revisions, or tasks student should complete (visible to student)...'
            }),
            'private_notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Internal faculty notes, grading observations, or confidential remarks (NOT visible to student)...'
            }),
        }
