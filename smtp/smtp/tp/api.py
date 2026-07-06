from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.authtoken.views import obtain_auth_token
from django.shortcuts import get_object_or_404

from .permissions import IsInstructorOrReadOnly
from .models import Course, Lesson, Payment
from .serializers import CourseSerializer, LessonSerializer, PaymentSerializer
from .payments import create_order, verify_payment_signature


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsInstructorOrReadOnly,)

    def perform_create(self, serializer):
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            serializer.save(instructor=user)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        course = self.get_object()
        course.restore()
        return Response(self.get_serializer(course).data)

    @action(detail=True, methods=['delete'])
    def hard_delete(self, request, pk=None):
        course = self.get_object()
        course.hard_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsInstructorOrReadOnly,)


class PaymentViewSet(viewsets.GenericViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @action(detail=False, methods=['post'])
    def create_order(self, request):
        course_id = request.data.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        if course.price <= 0:
            return Response({'detail': 'Course is free or price is not set'}, status=status.HTTP_400_BAD_REQUEST)

        order = create_order(course.price, receipt=f'course_{course.id}_user_{request.user.id}', notes={'course': course.title})
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            amount=course.price,
            currency='INR',
            status='created',
            razorpay_order_id=order.get('id'),
        )
        return Response({'order': order, 'payment_id': payment.id})

    @action(detail=False, methods=['post'])
    def verify(self, request):
        order_id = request.data.get('razorpay_order_id')
        payment_id = request.data.get('razorpay_payment_id')
        signature = request.data.get('razorpay_signature')
        payment = get_object_or_404(Payment, razorpay_order_id=order_id)

        try:
            verify_payment_signature(order_id, payment_id, signature)
            payment.mark_paid(payment_id, signature)
            return Response({'detail': 'Payment verified', 'status': payment.status})
        except Exception as exc:
            payment.mark_failed()
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        role = request.data.get('role', 'student')
        email = request.data.get('email', '')
        if not username or not password:
            return Response({'detail': 'username and password required'}, status=status.HTTP_400_BAD_REQUEST)

        user = Course._meta.apps.get_model('tp', 'User').objects.create_user(
            username=username,
            password=password,
            email=email,
            role=role,
        )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'username': user.username, 'role': user.role}, status=status.HTTP_201_CREATED)
