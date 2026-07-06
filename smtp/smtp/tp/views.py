import json

from django.urls import reverse_lazy, reverse
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse
from django.conf import settings

from .models import Course, Lesson, Payment
from .serializers import CourseSerializer
from .forms import RegisterForm, CourseForm
from .payments import create_order, verify_payment_signature, verify_webhook_signature


class HomeView(generic.TemplateView):
	template_name = "tp/index.html"


class CourseListView(generic.ListView):
	model = Course
	template_name = "tp/course_list.html"
	context_object_name = "courses"
	paginate_by = 9


class CourseDetailView(generic.DetailView):
	model = Course
	template_name = "tp/course_detail.html"
	context_object_name = "course"


class CourseCreateView(LoginRequiredMixin, generic.CreateView):
	model = Course
	form_class = CourseForm
	template_name = "tp/course_form.html"

	def form_valid(self, form):
		form.instance.instructor = self.request.user
		return super().form_valid(form)

	def get_success_url(self):
		return reverse('tp:course_detail', kwargs={'pk': self.object.pk})


class CourseUpdateView(LoginRequiredMixin, generic.UpdateView):
	model = Course
	form_class = CourseForm
	template_name = "tp/course_form.html"

	def get_success_url(self):
		return reverse('tp:course_detail', kwargs={'pk': self.object.pk})


class CourseDeleteView(LoginRequiredMixin, generic.View):
	def post(self, request, pk):
		course = get_object_or_404(Course, pk=pk)
		course.delete()
		return redirect('tp:course_list')


class CoursePurchaseView(LoginRequiredMixin, generic.TemplateView):
	template_name = "tp/course_purchase.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		course = get_object_or_404(Course, pk=self.kwargs.get('pk'))
		context['course'] = course
		context['razorpay_key_id'] = settings.RAZORPAY_KEY_ID
		return context

	def post(self, request, *args, **kwargs):
		course = get_object_or_404(Course, pk=self.kwargs.get('pk'))
		if request.content_type == 'application/json':
			data = json.loads(request.body.decode('utf-8'))
			order_id = data.get('razorpay_order_id')
			payment_id = data.get('razorpay_payment_id')
			signature = data.get('razorpay_signature')
			payment = get_object_or_404(Payment, razorpay_order_id=order_id, user=request.user)

			try:
				verify_payment_signature(order_id, payment_id, signature)
				payment.mark_paid(payment_id, signature)
				return JsonResponse({'detail': 'Payment verified', 'status': payment.status})
			except Exception as exc:
				payment.mark_failed()
				return JsonResponse({'detail': str(exc)}, status=400)

		if course.price <= 0:
			return redirect('tp:course_detail', pk=course.pk)

		order = create_order(course.price, receipt=f'course_{course.id}_user_{request.user.id}', notes={'course': course.title})
		payment = Payment.objects.create(
			user=request.user,
			course=course,
			amount=course.price,
			currency='INR',
			status='created',
			razorpay_order_id=order.get('id'),
		)

		context = self.get_context_data(**kwargs)
		context['order'] = order
		context['payment'] = payment
		return self.render_to_response(context)


class RazorpayWebhookView(generic.View):
	@method_decorator(csrf_exempt)
	def dispatch(self, request, *args, **kwargs):
		return super().dispatch(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')
		secret = settings.RAZORPAY_WEBHOOK_SECRET
		if not signature or not secret:
			return HttpResponse(status=400)

		try:
			verify_webhook_signature(request.body, signature, secret)
		except Exception:
			return HttpResponse(status=400)

		payload = json.loads(request.body.decode('utf-8'))
		event = payload.get('event')
		payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
		order_id = payment_entity.get('order_id')
		payment_id = payment_entity.get('id')
		payment_status = payment_entity.get('status')
		payment = Payment.objects.filter(razorpay_order_id=order_id).first()
		if payment and payment_status == 'captured':
			payment.mark_paid(payment_id, signature)
		elif payment:
			payment.mark_failed()
		return HttpResponse(status=200)


class LessonDetailView(generic.DetailView):
	model = Lesson
	template_name = "tp/lesson_detail.html"
	context_object_name = "lesson"


class LessonCreateView(LoginRequiredMixin, generic.CreateView):
	model = Lesson
	fields = ["title", "content", "order", "duration_seconds"]
	template_name = "tp/lesson_form.html"

	def form_valid(self, form):
		course_pk = self.kwargs.get("course_pk")
		form.instance.course = get_object_or_404(Course, pk=course_pk)
		return super().form_valid(form)

	def get_success_url(self):
		return reverse('tp:course_detail', kwargs={'pk': self.object.course_id})


class LessonUpdateView(LoginRequiredMixin, generic.UpdateView):
	model = Lesson
	fields = ["title", "content", "order", "duration_seconds"]
	template_name = "tp/lesson_form.html"

	def get_success_url(self):
		return reverse('tp:lesson_detail', kwargs={'pk': self.object.pk})


class LessonDeleteView(LoginRequiredMixin, generic.View):
	def post(self, request, pk):
		lesson = get_object_or_404(Lesson, pk=pk)
		lesson.delete()
		return redirect("tp:course_detail", pk=lesson.course_id)


class RegisterView(generic.FormView):
	template_name = 'tp/register.html'
	form_class = RegisterForm
	success_url = reverse_lazy('tp:course_list')

	def form_valid(self, form):
		user = form.save()
		login(self.request, user)
		return super().form_valid(form)


