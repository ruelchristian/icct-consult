from django import forms
from .models import SessionRecord

INPUT_STYLE = 'background-color: #ffffff !important; color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; caret-color: #0a315a !important;'
SELECT_CLS = 'w-full px-3 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 focus:bg-white focus:text-slate-900 focus:border-[#0a315a] focus:ring-2 focus:ring-[#0a315a]/20 focus:outline-none transition text-base'
TEXTAREA_CLS = 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 placeholder-slate-400 focus:bg-white focus:text-slate-900 focus:border-[#0a315a] focus:ring-2 focus:ring-[#0a315a]/20 focus:outline-none transition text-base'

class SessionRecordForm(forms.ModelForm):
    class Meta:
        model = SessionRecord
        fields = ['attendance', 'advice_given', 'action_items', 'private_notes']
        widgets = {
            'attendance': forms.Select(attrs={'class': SELECT_CLS, 'style': INPUT_STYLE}),
            'advice_given': forms.Textarea(attrs={
                'class': TEXTAREA_CLS,
                'style': INPUT_STYLE,
                'rows': 4,
                'placeholder': 'Key guidance, explanations, recommendations, or feedback for the student (visible to student)...'
            }),
            'action_items': forms.Textarea(attrs={
                'class': TEXTAREA_CLS,
                'style': INPUT_STYLE,
                'rows': 3,
                'placeholder': 'Deliverables, revisions, or tasks student should complete (visible to student)...'
            }),
            'private_notes': forms.Textarea(attrs={
                'class': TEXTAREA_CLS,
                'style': INPUT_STYLE,
                'rows': 3,
                'placeholder': 'Internal faculty notes, grading observations, or confidential remarks (NOT visible to student)...'
            }),
        }
