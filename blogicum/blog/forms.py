from django import forms
from django.contrib.auth import get_user_model
from django.forms import DateTimeInput

from . import models


class PostForm(forms.ModelForm):

    class Meta:
        model = models.Post
        exclude = ('author', )


class ProfileForm(forms.ModelForm):

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'username', 'email')


class CommentForm(forms.ModelForm):

    class Meta:
        model = models.Comment
        fields = ('text',)