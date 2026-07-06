from rest_framework import serializers

from .models import Course, Lesson, User, Payment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role")


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ("id", "course", "title", "content", "order", "duration_seconds", "is_deleted")
        read_only_fields = ("is_deleted",)


class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    instructor = UserSerializer(read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "slug",
            "image_url",
            "price",
            "description",
            "instructor",
            "lessons",
            "created_at",
            "updated_at",
            "is_deleted",
        )
        read_only_fields = ("is_deleted", "created_at", "updated_at")


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "user",
            "course",
            "amount",
            "currency",
            "status",
            "razorpay_order_id",
            "razorpay_payment_id",
            "razorpay_signature",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("status", "created_at", "updated_at")
