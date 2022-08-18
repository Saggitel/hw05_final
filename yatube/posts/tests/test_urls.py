from django.test import TestCase, Client
from http import HTTPStatus
from django.urls import reverse


from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        url_names = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug
            }): HTTPStatus.OK,
            reverse('posts:profile', kwargs={
                'username': self.user
            }): HTTPStatus.OK,
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.id
            }): HTTPStatus.OK,
        }
        for url, status in url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

                
    def test_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизированному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница /profile/<post_id>/edit/ доступна автору поста."""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница /profile/<post_id>/edit/ перенаправит анонимного
         пользователя на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next='
            f'/posts/{self.post.id}/edit/'
        )

    def test_create_url_redirect_anonymous_on_auth_login(self):
        """Страница /create/ перенаправит анонимного
         пользователя на страницу логина.
        """
        response = self.guest_client.get(
            '/create/', follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_unexisting_page_url_response_not_found(self):
        """Запрос к страница unixisting_page вернет ошибку 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница /posts/<post_id>/comment/
        перенаправит анонимного пользователя на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.id}/comment/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next='
            f'/posts/{self.post.id}/comment/'
        )