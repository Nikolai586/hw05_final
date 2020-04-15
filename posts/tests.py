from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import Post, Group, Follow, Comment
from .forms import CommentForm
import time

User = get_user_model()

# Create your tests here.
class ProfileTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='koya', email='koya@koya.ru', password='123456')
        self.client.force_login(self.user)

    def test_profile(self):
        respons = self.client.get(f'/{self.user.username}/')
        self.assertEqual(respons.status_code, 200)

    def test_post(self):
        response = self.client.post('/new', {'text':'это пост'}, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_post_logout(self):
        self.client.logout()
        respons = self.client.post('/new', {'text': 'Это мой тредтий пост'}, follow=True)
        self.assertRedirects(respons, '/auth/login/?next=/new', status_code=302, target_status_code=200)

    def test_post_index(self):
        text = 'Это тоже пост'
        post = Post.objects.create(text=text, author=self.user)
        response = self.client.get('/')
        self.assertContains(response, text)
        response = self.client.get(f'/{post.author}/')
        self.assertContains(response, text)
        response = self.client.get(f'/{post.author}/{post.id}/')
        self.assertContains(response, text)

    def test_post_edit(self):
        post = Post.objects.create(text = "Редакт пост", author = self.user)
        new_text = 'это изменения'
        response = self.client.post(f'/{self.user.username}/{post.id}/edit/', {'text': new_text}, follow=True)
        self.assertContains(response, new_text)
        response = self.client.post(f'/{self.user.username}/')
        self.assertContains(response, new_text)
        response = self.client.post('/')
        self.assertContains(response, new_text)

    def test_404(self):
        response = self.client.get('/ruk/3/')
        self.assertEqual(response.status_code, 404)

class Test_img(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='Tor', email='boggroma@asgart.ru', password='123456')
        self.group = Group.objects.create(title='MARVEL', slug='asgart', description='the world of MARVEL')
        self.post = Post.objects.create(text='Я бог грома', author=self.user, group=self.group)
        self.client.force_login(self.user)

    def test_img(self):
        with open('media/posts/image1.jpg', 'rb') as fr:
            self.client.post(f'/{self.user.username}/{self.post.id}/edit/', {'text': self.post.text, 'group': self.group.id, 'image': fr})
        response = self.client.get(f'/{self.user.username}/{self.post.id}/')
        self.assertContains(response, '<img')

    def test_img_pages(self):
        with open('media/posts/image1.jpg', 'rb') as fr:
            self.client.post(f'/{self.user.username}/{self.post.id}/edit/', {'text': self.post.text, 'group': self.group.id, 'image': fr})
        response = self.client.get('/')
        self.assertContains(response, '<img')
        response = self.client.get(f'/{self.user.username}/')
        self.assertContains(response, '<img')
        response = self.client.get(f'/group/{self.group.slug}/')
        self.assertContains(response, '<img')
        self.assertEqual(response.status_code, 200)

    def test_img_load(self):
        with open('media/posts/fas.txt', 'rb') as fr:
            self.client.post(f'/{self.user.username}/{self.post.id}/edit/', {'text': self.post.text, 'image': fr})
        response = self.client.get(f'/{self.user.username}/{self.post.id}/')
        self.assertNotContains(response, '<img')

class Cache(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='Tor', email='boggroma@asgart.ru', password='123456')
        self.client.force_login(self.user)

    def test_cache(self):
        response = self.client.get('/')
        self.text = 'Я бог грома'
        self.post = Post.objects.create(text=self.text , author=self.user)
        self.assertNotContains(response, self.text)
        time.sleep(20)
        response = self.client.get('/')
        self.assertContains(response, self.text)

class Follow_test(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='Tor', email='boggroma@asgart.ru', password='123456')
        self.user2 = User.objects.create_user(username='Odin', email='bog@asgart.ru', password='1234567')
        self.user3 = User.objects.create_user(username='Halk', email='green@asgart.ru', password='12345678')
        Follow.objects.create(user=self.user2, author=self.user)
        self.text = 'это текст'
        self.post = Post.objects.create(text=self.text, author=self.user)
        self.client.force_login(self.user2)

    def test_follow(self):
        response = self.client.get('/follow/')
        self.assertContains(response, self.text)
        Follow.objects.filter(user=self.user2, author=self.user).delete()
        response = self.client.get('/follow/')
        self.assertNotContains(response, self.text)

    def test_follow_2(self):
        self.text_2 = 'это еще один пост'
        Post.objects.create(text=self.text_2, author=self.user)
        response = self.client.get('/follow/')
        self.assertContains(response, self.text_2)
        self.client.logout()
        self.client.force_login(self.user3)
        response = self.client.get('/follow/')
        self.assertNotContains(response, self.text_2)

    def test_comment(self):
        self.text_comment = 'это комментарий'
        self.client.post(f'/{self.user.username}/{self.post.id}/comment/', {'text': self.text_comment}, follow=True)
        response = self.client.get(f'/{self.user.username}/{self.post.id}/')
        self.assertContains(response, self.text_comment)
        self.client.logout()
        self.text_comment_2 = 'это второй коментарий'
        self.client.post(f'/{self.user.username}/{self.post.id}/comment/', {'text': self.text_comment_2}, follow=True)
        response = self.client.get(f'/{self.user.username}/{self.post.id}/')
        self.assertNotContains(response, self.text_comment_2)

