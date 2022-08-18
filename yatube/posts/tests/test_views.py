from django import forms
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User, Comment, Follow
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from posts.views import NUMBER_OF_POSTS


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.user = User.objects.create_user(username='test_user')
        cls.another_user = User.objects.create_user(
            username='Автор комментария'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )    
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.another_user,
            text='Тестовый текст комментария'
        )
        cls.second_user = User.objects.create_user(username='test_second_user')
        cls.second_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание 2',
        )
        cls.second_post = Post.objects.create(
            author=cls.second_user,
            text='Тестовый текст 2',
            group=cls.second_group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:profile', kwargs={
                'username': self.user
            }): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.id
            }): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id
            }): 'posts/create_post.html',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug
            }): 'posts/group_list.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_uses_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.context['page_obj']
        for post in posts:
            if post.author == self.user:
                post_text = post.text
                post_author = post.author
                post_group = post.group.title
                post_image = post.image
                self.assertEqual(post_text, self.post.text)
                self.assertEqual(post_author, self.user)
                self.assertEqual(post_group, self.group.title)
                self.assertEqual(post_image, self.post.image)

    def test_group_posts_uses_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug
            }))
        posts = response.context['page_obj']
        for post in posts:
            if post.author == self.user:
                post_text = post.text
                post_image = post.image
                post_group_title = post.group.title
                post_group_slug = post.group.slug
                post_group_description = post.group.description
                self.assertEqual(post_text, self.post.text)
                self.assertEqual(post_image, self.post.image)
                self.assertEqual(post_group_title, self.group.title)
                self.assertEqual(post_group_slug, self.group.slug)
                self.assertEqual(
                    post_group_description, self.group.description
                )

    def test_profile_uses_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={
                'username': self.user
            }))
        posts = response.context['page_obj']
        for post in posts:
            if post.author == self.user:
                post_author = post.author
                post_title = f'Профайл пользователя {post.author}'
                post_image = post.image
                self.assertEqual(post_author, self.user)
                self.assertEqual(
                    post_title, f'Профайл пользователя {self.user}'
                )
                self.assertEqual(post_image, self.post.image)

    def test_post_detail_uses_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        NUM_OF_TEXTS_SYMBOLS_IN_TITLE = 30
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': f'{self.post.id}'
            }))
        post = response.context['post']
        if post.author == self.user:
            post_title = post.text[:NUM_OF_TEXTS_SYMBOLS_IN_TITLE]
            post_image = post.image
            self.assertEqual(
                post_title, self.post.text[:NUM_OF_TEXTS_SYMBOLS_IN_TITLE]
            )
            self.assertEqual(post, self.post)
            self.assertEqual(post_image, self.post.image)

    def test_post_create_uses_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_uses_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id
            })
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pages_show_the_post_with_the_group(self):
        """На страницах index, group_list, profile отображается пост
        с указанной группой.
        """
        post_with_group = self.post
        reverse_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user})
        ]
        for reverse_name in reverse_names:
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertIn(
                    post_with_group, response.context['page_obj']
                )

    def test_post_is_not_in_the_wrong_group(self):
        """Пост с указанной группой не попал в другую группу."""
        post_with_group = self.post
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={
                'slug': self.second_group.slug}
            )
        )
        self.assertNotIn(
            post_with_group, response.context['page_obj']
        )





    def test_post_detail_show_the_comment(self):
        """На страницах post_detail отображается
        комментарий к посту.
        """
        comment = self.comment
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': f'{self.post.id}'}
            ))
        self.assertIn(comment, response.context['comments'])


class PaginatorViewsTest(TestCase):

    BATCH_SIZE = 13

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_second_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',)
        object_list = [
            Post(
                author=cls.user,
                text=f'Текст объекта {i}',
                group=cls.group
            )
            for i in range(cls.BATCH_SIZE)
        ]
        cls.posts_to_check = Post.objects.bulk_create(object_list)

    def setUp(self):
        self.guest_client = Client()

    def test_num_of_posts_on_the_pages_is_correct(self):
        """
        Проверка пажинатора. На первой странице index,
         group_list, profile отображается 10 постов.
         На второй - остальные созданные в фикстурах посты.
        """
        NUM_OF_POSTS_2ND_PAGE = PaginatorViewsTest.BATCH_SIZE - NUMBER_OF_POSTS
        reverse_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}),
            reverse('posts:profile', kwargs={'username': f'{self.user}'})
        ]
        for reverse_name in reverse_names:
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), NUMBER_OF_POSTS
                )
                response = self.guest_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']), NUM_OF_POSTS_2ND_PAGE
                )


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        new_small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=new_small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='cache_user')
        cls.group = Group.objects.create(
            title='Группа для тестирования кэша',
            slug='test_slug_cache',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
            group=cls.group,
            image=cls.uploaded
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        response = self.authorized_client.get(reverse('posts:index'))
        context = response.context['page_obj']
        content = response.content
        post = context[0]
        self.assertEqual(post.id, self.post.id)
        Post.objects.get(pk=post.id).delete()
        new_response = self.authorized_client.get(reverse('posts:index'))
        new_content = new_response.content
        self.assertEqual(content, new_content)
        cache.clear()
        new_new_response = self.authorized_client.get(reverse('posts:index'))
        new_new_content = new_new_response.content
        self.assertNotEqual(content, new_new_content)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_follower')
        cls.second_user = User.objects.create_user(username='test_following')
        cls.third_user = User.objects.create_user(username='test_not_follower')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_too = Client()
        self.authorized_client_too.force_login(self.third_user)

    def test_profile_follow_unfollow(self):
        """Авторизированный пользователь может
        подписываться на других пользователей и
        удалять их из подписок.
        """
        user = self.user
        following = user.following.count()
        author = self.second_user
        response = self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={
                'username': author.username
            }
            ),
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': author.username})
        )
        self.assertEqual(Follow.objects.count(), following + 1)
        new_response = self.authorized_client.post(
            reverse('posts:profile_unfollow', kwargs={
                'username': author.username
            }
            ),
        )
        self.assertRedirects(new_response, reverse(
            'posts:profile', kwargs={'username': author.username})
        )
        self.assertEqual(Follow.objects.count(), following)

    def test_follow_index(self):
        """Пост отображается только у подписчиков."""
        user = self.user
        author = self.second_user
        Follow.objects.create(user=user, author=author)
        group = Group.objects.create(
            title='Группа для тестирования follow index',
            slug='test_slug_follow',
            description='Пост должен отображаться',
        )
        post = Post.objects.create(
            author=author,
            text='Тест отображения постов',
            group=group,
        )
        response = self.authorized_client.post(
            reverse('posts:follow_index'))
        self.assertIn(
            post, response.context['page_obj']
        )
        response = self.authorized_client_too.post(
            reverse('posts:follow_index'))
        self.assertNotIn(
            post, response.context['page_obj']
        )
