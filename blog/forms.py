from django import forms

class PostCommentForm(forms.Form):
    name = forms.CharField(max_length=64, label='Name (required)')
    email = forms.EmailField(required=False, label='Email')
    url = forms.URLField(required=False, label='Website')
    content = forms.CharField(widget=forms.Textarea, label='')
    password = forms.CharField(label='Input the captcha password')

