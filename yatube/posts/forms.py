from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст',
                  'group': 'Группа'}
        help_text = {'text': 'Введите текст',
                     'group': 'Выберите группу'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Текст комментария'}
        help_texts = {'text': 'Hапишите свой комментарий здесь'}
        widgets = {'text': forms.Textarea({'rows': 3})}
