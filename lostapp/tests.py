from django.contrib.auth.models import User
from django.test import TestCase
from .models import Author, Post
from django.urls import reverse
import json
from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Author, Post, Comment,Like
from rest_framework.test import APIRequestFactory
from lostapp.views import likes,signup

from django.test import RequestFactory





class AuthorModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_author_creation(self):
        author = Author.objects.create(user=self.user, display_name='Test Author')
        self.assertEqual(author.user, self.user)
        self.assertEqual(author.display_name, 'Test Author')


class PostModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.author = Author.objects.create(user=self.user, display_name='Test Author')

    def test_post_creation(self):
        post = Post.objects.create(title='Test Post', author=self.author, content='Test content')
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.content, 'Test content')


class CommentModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.author = Author.objects.create(user=self.user, display_name='Test Author')
        self.post = Post.objects.create(title='Test Post', author=self.author, content='Test content')

    def test_comment_creation(self):
        comment = Comment.objects.create(post=self.post, author=self.author, comment='Test comment')
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.author)
        self.assertEqual(comment.comment, 'Test comment')


class LikeModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.author = Author.objects.create(user=self.user, display_name='Test Author')
        self.post = Post.objects.create(title='Test Post', author=self.author, content='Test content')
        self.comment = Comment.objects.create(post=self.post, author=self.author, comment='Test comment')

    def test_like_post_creation(self):
        like = Like.objects.create(author=self.author, post=self.post)
        self.assertEqual(like.author, self.author)
        self.assertEqual(like.post, self.post)

    def test_like_comment_creation(self):
        like = Like.objects.create(author=self.author, comment=self.comment)
        self.assertEqual(like.author, self.author)
        self.assertEqual(like.comment, self.comment)







class SignupViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_signup_view_success(self):
        # Create a POST request with valid signup data
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword',
            'display_name': 'Test User',
            'github': 'https://github.com/testuser'
        }
        request = self.factory.post("/fake-url/", data)
        response = signup(request)
        
        # Check if the user was created and redirected to the login page
        self.assertEqual(response.status_code, 302)  # Redirect status code
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_signup_view_invalid_email(self):
        # Create a POST request with invalid email format
        data = {
            'username': 'testuser',
            'email': 'invalidemail',
            'password': 'testpassword',
            'display_name': 'Test User',
            'github': 'https://github.com/testuser'
        }
        request = self.factory.post("/fake-url/", data)
        response = signup(request)
        
        # Check if the view returns the signup page with an error message
        self.assertEqual(response.status_code, 200)  # OK status code
        self.assertContains(response, "Invalid email format.")

    def test_signup_view_existing_email(self):
        # Create a user with an existing email
        User.objects.create_user(username='existinguser', email='test@example.com', password='password')
        
        # Attempt to sign up with the same email
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword',
            'display_name': 'Test User',
            'github': 'https://github.com/testuser'
        }
        request = self.factory.post("/fake-url/", data)
        response = signup(request)
        
        # Check if the view returns the signup page with an error message
        self.assertEqual(response.status_code, 200)  # OK status code
        self.assertContains(response, "Email is already associated with an existing account.")

    def test_signup_view_existing_username(self):
        # Create a user with an existing username
        User.objects.create_user(username='existinguser', email='existing@example.com', password='password')
        
        # Attempt to sign up with the same username
        data = {
            'username': 'existinguser',
            'email': 'test@example.com',
            'password': 'testpassword',
            'display_name': 'Test User',
            'github': 'https://github.com/testuser'
        }
        request = self.factory.post("/fake-url/", data)
        response = signup(request)
        
        # Check if the view returns the signup page with an error message
        self.assertEqual(response.status_code, 200)  # OK status code
        self.assertContains(response, "Username is already taken.")



class LostAppViewsTestCase(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(username='testuser', password='testpassword')

        # Create an author
        self.author = Author.objects.create(user=self.user, display_name='Test Author')

        # Create a post
        self.post = Post.objects.create(title='Test Post', content='This is a test post', author=self.author)

    def test_author_profile_view(self):
        url = reverse('lostapp:author', args=[self.author.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authors/profile.html')

    def test_single_post_view_get(self):
        url = reverse('lostapp:single_post', args=[self.author.id, self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'single_post/index.html')

    def test_single_post_view_delete(self):
        self.client.force_login(self.user)  # Login as the post author
        url = reverse('lostapp:single_post', args=[self.author.id, self.post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 303)  # Redirect status code

    def test_single_post_view_put(self):
        self.client.force_login(self.user)  # Login as the post author
        url = reverse('lostapp:single_post', args=[self.author.id, self.post.id])
        data = {'title': 'Updated Post Title', 'content': 'Updated post content'}
        response = self.client.put(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 303)  # Redirect status code

    def test_follow_view(self):
        self.client.force_login(self.user)  # Login as a user
        url = reverse('lostapp:follow')
        data = {'author_id': self.author.id}
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'success', 'message': 'Followed successfully'})

    def test_unfollow_view(self):
        self.client.force_login(self.user)  # Login as a user
        self.author.followers.add(self.user.author)  # Make the user follow the author
        url = reverse('lostapp:unfollow')
        data = {'author_id': self.author.id}
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'success', 'message': 'Unfollowed successfully'})

    def test_fetch_follow_status_view(self):
        self.client.force_login(self.user)  # Login as a user
        self.author.followers.add(self.user.author)  # Make the user follow the author
        url = reverse('lostapp:fetch_follow_status')
        data = {'author_id': self.author.id}
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'is_following': False  })


class CommentsViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username='testuser')
        self.author = Author.objects.create(user=self.user, display_name='Test Author')
        self.post = Post.objects.create(
            title="Test Post",
            author=self.author,
            content="Test content",
            visibility=Post.Visibility.PUBLIC,
        )


    def test_comments_get(self):
        # Create a comment using the Author instance
        Comment.objects.create(post=self.post, author=self.author, comment='Test comment')

        # Perform GET request to fetch comments for the post
        url = reverse('lostapp:comments', kwargs={'author_id': self.author.id, 'post_id': self.post.id})
        response = self.client.get(url)

        # Check if the response contains the comment
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test comment')

    def test_comments_post_bad_comment(self):
        
        url = reverse('lostapp:comments', kwargs={'author_id': self.author.id, 'post_id': self.post.id})
        # Send invalid data to trigger an error
        data = {
            'author': {
                'display_name': 'Test Author',
                # Include other author fields if required
            },
            'comment': '',  # Empty comment field to trigger validation error
            'contentType': 'text/plain',
            'published': '2024-03-18T12:00:00Z',
            # Include other required fields as per your serializer
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)  # Expecting a validation error



    def test_invalid_comment_post(self):
        # Prepare invalid data for POST request (missing 'comment' field)
        invalid_data = {'contentType': 'text/markdown'}

        # Perform POST request with invalid data
        url = reverse('lostapp:comments', kwargs={'author_id': str(self.author.id), 'post_id': str(self.post.id)})
        response = self.client.post(url, invalid_data, format='json')

        # Check if the request fails with status 400 (Bad Request)
        self.assertEqual(response.status_code, 400)



class LikesViewTestCase(APITestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username='user1', password='testpassword')
        self.user2 = User.objects.create_user(username='user2', password='testpassword')

        # Create test authors, posts, and comments
        self.author1 = Author.objects.create(user=self.user1, display_name='User1')
        self.author2 = Author.objects.create(user=self.user2, display_name='User2')
        self.post = Post.objects.create(title='Test Post', author=self.author2, content='Test content')
        self.comment = Comment.objects.create(post=self.post, author=self.author2, comment='Test comment')

    def test_like_post(self):
        factory = APIRequestFactory()
        request = factory.post('/fake-url/', {'author_id': str(self.author2.id), 'post_id': str(self.post.id)})
        request.user = self.user1
        response = likes(request, author_id=self.author2.id, post_id=self.post.id)
        self.assertEqual(response.status_code, 303)  # Expected status code for successful like

    def test_like_own_post(self):
        factory = APIRequestFactory()
        request = factory.post('/fake-url/', {'author_id': str(self.author2.id), 'post_id': str(self.post.id)})
        request.user = self.user2
        response = likes(request, author_id=self.author2.id, post_id=self.post.id)
        self.assertEqual(response.status_code, 403)  # Expected status code for own post liking

    def test_like_comment(self):
        factory = APIRequestFactory()
        request = factory.post('/fake-url/', {'author_id': str(self.author2.id), 'post_id': str(self.post.id), 'comment_id': str(self.comment.id)})
        request.user = self.user1
        response = likes(request, author_id=self.author2.id, post_id=self.post.id, comment_id=self.comment.id)
        self.assertEqual(response.status_code, 303)  # Expected status code for successful like

    def test_like_own_comment(self):
        factory = APIRequestFactory()
        request = factory.post('/fake-url/', {'author_id': str(self.author2.id), 'post_id': str(self.post.id), 'comment_id': str(self.comment.id)})
        request.user = self.user2
        response = likes(request, author_id=self.author2.id, post_id=self.post.id, comment_id=self.comment.id)
        self.assertEqual(response.status_code, 403) 