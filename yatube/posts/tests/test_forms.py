import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm
from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='newname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test4',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Какой-то не очень оригинальный коммент',
        )
        cls.form = CommentForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает Post и сохраняет его в БД."""
        posts_count = Post.objects.count()
        small_image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_image,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст поста',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': f'{self.user.username}'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Текст поста',
                group=1,
                image='posts/small.gif',
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма позволяет редактировать Post
        и сохраняет его изменения в БД."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': f'{self.post.pk}'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': f'{self.post.pk}'}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Отредактированный текст поста',
                group=1
            ).exists()
        )

    def test_detail_show_comment(self):
        """Зарегистрированный пользователь может оставлять
        комментарии и они сохраняются на странице поста."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': self.comment.text
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': f'{self.post.pk}'}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Какой-то не очень оригинальный коммент',
            ).exists()
        )

    def test_detail_show_comment2(self):
        """Незарегистрированный пользователь
        не может оставлять комментарии."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': self.comment.text
        }
        response = self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertEqual(response.status_code, 200)
