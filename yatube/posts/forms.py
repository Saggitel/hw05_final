from xml.etree.ElementTree import Comment

from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {'text': 'Введите сообщение', 'group': 'Выберите группу'}
        labels = {'text': 'Текст сообщения', 'group': 'Группа'}


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {'text': 'Напишиет свой коментарий'}
        labels = {'text': 'Текст'}
