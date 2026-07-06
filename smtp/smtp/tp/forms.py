from django import forms
from django.contrib.auth import get_user_model

from .cloudinary_utils import upload_image


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=(('student', 'Student'), ('instructor', 'Instructor')))

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match')
        return cleaned

    def save(self):
        User = get_user_model()
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['username'],
            email=data.get('email', ''),
            password=data['password1'],
            role=data.get('role', 'student'),
        )
        return user


from .models import Course


class CourseForm(forms.ModelForm):
    image_file = forms.FileField(required=False, help_text='Upload an image file to Cloudinary')

    class Meta:
        model = Course
        fields = ['title', 'slug', 'image_url', 'description', 'price']

    def save(self, commit=True):
        instance = super().save(commit=False)
        image_file = self.cleaned_data.get('image_file')
        if image_file:
            image_url = upload_image(image_file, folder='tp_courses')
            instance.image_url = image_url
        if commit:
            instance.save()
        return instance
