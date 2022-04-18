import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

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


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='newname')
        cls.user2 = User.objects.create_user(username='username')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Группа для задания 3',
            slug='test3',
            description='очень много букаф'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
            image='posts/small.gif'
        )
        # cls.post_follow = Post.objects.create(
        #     author=cls.user2,
        #     text='Тестовый пост для проверки подписок',
        # )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Какой-то не очень оригинальный коммент',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_follow = Client()
        self.authorized_client_follow.force_login(self.user2)
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list',
                        kwargs={'slug': f'{self.group.slug}'})
            ),
            'posts/profile.html': (
                reverse('posts:profile',
                        kwargs={'username': f'{self.user.username}'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail',
                        kwargs={'post_id': f'{self.post.pk}'})
            ),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_author_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'posts/create_post.html': (
                reverse('posts:post_edit',
                        kwargs={'post_id': f'{self.post.pk}'})
            ),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_and_group_page_and_profile_show_correct_context(self):
        """Шаблоны index, group_list и profile
        сформированы с правильным контекстом."""
        templates_context = {
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}),
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}),
        }
        for template_context in templates_context:
            with self.subTest(template_context=template_context):
                response = self.authorized_client.get(template_context)
                first_post = response.context.get('page_obj')[0]
                self.assertEqual(
                    first_post.text,
                    self.post.text)
                self.assertEqual(
                    first_post.author.username,
                    self.post.author.username)
                self.assertEqual(
                    first_post.group.title,
                    self.post.group.title)
                self.assertNotEqual(
                    first_post.group.title,
                    self.group2.title)
                self.assertEqual(
                    first_post.pub_date,
                    self.post.pub_date)
                self.assertEqual(
                    first_post.image,
                    self.post.image)

    def test_detail_show_correct_context(self):
        """Для авторизованного пользователя
        в шаблон post_detail  передается пост с нужным контекстом."""
        response = (self.authorized_client.get
                    (reverse('posts:post_detail',
                     kwargs={'post_id': f'{self.post.id}'})))
        this_post = response.context.get('post')
        self.assertEqual(
            this_post.text,
            self.post.text)
        self.assertEqual(
            this_post.author.username,
            self.post.author.username)
        self.assertNotEqual(
            this_post.group.title,
            self.group2.title)
        self.assertEqual(
            this_post.pub_date,
            self.post.pub_date)
        self.assertEqual(
            this_post.image,
            self.post.image)

        form_fields = {
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_show_correct_context(self):
        """Шаблон create для создания поста сформирован
        с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_show_correct_context(self):
        """Шаблон create для редактирования поста сформирован
        с правильным контекстом."""
        response = (self.author_client.get
                    (reverse('posts:post_edit',
                     kwargs={'post_id': f'{self.post.pk}'})))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_cache(self):
        """Шаблон index кешируется."""
        response_before = self.author_client.get(reverse('posts:index'))
        cache_before = response_before.content
        Post.objects.create(
            author=self.user,
            text='текст для теста кеша',
            group=self.group,
        )
        response_after = self.author_client.get(reverse('posts:index'))
        cache_after = response_after.content
        self.assertEqual(cache_before, cache_after)
        cache.clear()
        response_after = self.author_client.get(reverse('posts:index'))
        cache_after = response_after.content
        self.assertNotEqual(cache_before, cache_after)

    def test_follow_author(self):
        """Зарегистрированный пользователь может
        подписаться и отписываться от авторов."""
        follow_count_before = Follow.objects.count()
        self.authorized_client_follow.get(
            reverse('posts:profile_follow',
                    kwargs={'username': f'{self.user.username}'}))
        follow_count_after = Follow.objects.count()
        self.assertEqual(follow_count_after, follow_count_before + 1)
        self.authorized_client_follow.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': f'{self.user.username}'}))
        follow_count_after = Follow.objects.count()
        self.assertEqual(follow_count_after, follow_count_before)

    def test_follow_author2(self):
        """Незарегистрированный пользователь не может
        подписаться на авторов."""
        follow_count_before = Follow.objects.count()
        self.guest_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': f'{self.user.username}'}))
        follow_count_after = Follow.objects.count()
        self.assertEqual(follow_count_after, follow_count_before)

    def test_feed(self):
        """Пост понравившегося автора появляется в ленте у подписчика
        с правильным контекстом."""
        self.authorized_client_follow.get(
            reverse('posts:profile_follow',
                    kwargs={'username': f'{self.user.username}'}))
        response = self.authorized_client_follow.get(
            reverse('posts:follow_index'))
        first_post = response.context.get('page_obj')[0]
        self.assertEqual(
            first_post.text,
            self.post.text)
        self.assertEqual(
            first_post.author.username,
            self.post.author.username)
        self.assertEqual(
            first_post.group.title,
            self.post.group.title)
        self.assertNotEqual(
            first_post.group.title,
            self.group2.title)
        self.assertEqual(
            first_post.pub_date,
            self.post.pub_date)
        self.assertEqual(
            first_post.image,
            self.post.image)

    def test_feed2(self):
        """Пост понравившегося автора не появляется в ленте,
        если нет подписки."""
        self.authorized_client_follow.get(
            reverse('posts:profile_follow',
                    kwargs={'username': f'{self.user2.username}'}))
        response = self.authorized_client_follow.get(
            reverse('posts:follow_index'))
        self.assertNotContains(
            response,
            self.post.text)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='paginname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = []
        for i in range(1, 14):
            cls.post.append(Post.objects.create(
                            author=cls.user,
                            text=f'Тестовая пост №{i}',
                            group=cls.group,))

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Проверка пагинатора страниц index, group и profile
        для первых 10 постов."""
        templates_context = {
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}),
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'})
        }
        for template_context in templates_context:
            with self.subTest(template_context=template_context):
                response = self.authorized_client.get(template_context)
        self.assertEqual(len(response.context.get('page_obj')), 10)

    def test_second_page_contains_three_records(self):
        """Проверка пагинатора страниц index, group и profile
        для оставшихся 3 постов."""
        templates_context = {
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}),
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'})
        }
        for template_context in templates_context:
            with self.subTest(template_context=template_context):
                response = (self.authorized_client.get
                            (template_context + '?page=2'))

        self.assertEqual(len(response.context.get('page_obj')), 3)
