from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'star-radio'}),
    )

    class Meta:
        model  = Review
        fields = ['rating', 'title', 'comment', 'photo']
        widgets = {
            'title':   forms.TextInput(attrs={'placeholder': 'Brief summary of your review'}),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your detailed review...'}),
        }