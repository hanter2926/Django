from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .models import Course


class APITest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.instructor = User.objects.create_user(username='inst', password='pass', role='instructor')
        self.student = User.objects.create_user(username='stud', password='pass', role='student')

        # Obtain tokens
        client = APIClient()
        r = client.post('/api/auth/token/', {'username': 'inst', 'password': 'pass'})
        self.assertEqual(r.status_code, 200)
        self.inst_token = r.data['token']

        r = client.post('/api/auth/token/', {'username': 'stud', 'password': 'pass'})
        self.assertEqual(r.status_code, 200)
        self.stud_token = r.data['token']

    def test_student_cannot_create_course(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.stud_token)
        resp = client.post('/api/courses/', {'title': 'X', 'slug': 'x', 'description': 'd'})
        self.assertIn(resp.status_code, (403, 401))

    def test_instructor_can_create_and_delete_course(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + self.inst_token)
        resp = client.post('/api/courses/', {'title': 'Course1', 'slug': 'course1', 'description': 'd'})
        self.assertEqual(resp.status_code, 201)
        course_id = resp.data['id']

        # Delete (soft)
        resp = client.delete(f'/api/courses/{course_id}/')
        self.assertEqual(resp.status_code, 204)
        # Ensure not in default queryset
        self.assertFalse(Course.objects.filter(id=course_id).exists())
        # Exists in all_objects
        self.assertTrue(Course.all_objects.filter(id=course_id).exists())
