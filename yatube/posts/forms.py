from django.forms import ModelForm
from xml.etree.ElementTree import Comment
from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group','image')
        help_texts = {'text': 'Введите сообщение', 'group': 'Выберите группу'}
        labels = {'text': 'Текст сообщения', 'group': 'Группа'}

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
