from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
	class Role(models.TextChoices):
		ADMIN = "admin", "Admin"
		INSTRUCTOR = "instructor", "Instructor"
		STUDENT = "student", "Student"

	role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)


from django.db.models.query import QuerySet


class SoftDeleteQuerySet(QuerySet):
	def delete(self):
		# bulk soft-delete (updates rows instead of removing them)
		return super().update(is_deleted=True, deleted_at=timezone.now())

	def hard_delete(self):
		return super().delete()

	def restore(self):
		return super().update(is_deleted=False, deleted_at=None)

	def alive(self):
		return self.filter(is_deleted=False)

	def deleted(self):
		return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
	def get_queryset(self):
		return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
	def get_queryset(self):
		return super().get_queryset()


class SoftDeleteModel(models.Model):
	is_deleted = models.BooleanField(default=False)
	deleted_at = models.DateTimeField(null=True, blank=True)

	objects = SoftDeleteManager()
	all_objects = AllObjectsManager()

	class Meta:
		abstract = True

	def delete(self, using=None, keep_parents=False):
		if not self.is_deleted:
			self.is_deleted = True
			self.deleted_at = timezone.now()
			self.save(update_fields=["is_deleted", "deleted_at"])

	def hard_delete(self, using=None, keep_parents=False):
		super().delete(using=using, keep_parents=keep_parents)

	def restore(self):
		if self.is_deleted:
			self.is_deleted = False
			self.deleted_at = None
			self.save(update_fields=["is_deleted", "deleted_at"])


class Course(SoftDeleteModel):
	title = models.CharField(max_length=255)
	slug = models.SlugField(max_length=255, unique=True)
	image_url = models.URLField(blank=True, null=True, help_text='Optional Cloudinary image URL')
	price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Course price in INR')
	description = models.TextField(blank=True)
	instructor = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		related_name="courses",
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-created_at",)

	def delete(self, using=None, keep_parents=False):
		if not self.is_deleted:
			# soft-delete the course itself
			self.is_deleted = True
			self.deleted_at = timezone.now()
			self.save(update_fields=["is_deleted", "deleted_at"])
			# bulk soft-delete related lessons for efficiency
			now = timezone.now()
			self.lessons.filter(is_deleted=False).update(is_deleted=True, deleted_at=now)


class Lesson(SoftDeleteModel):
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
	title = models.CharField(max_length=255)
	content = models.TextField(blank=True)
	order = models.PositiveIntegerField(default=0)
	duration_seconds = models.PositiveIntegerField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("order",)
		constraints = [
			models.UniqueConstraint(fields=["course", "order"], name="unique_lesson_order_per_course")
		]


class Payment(models.Model):
	STATUS_CHOICES = [
		('created', 'Created'),
		('paid', 'Paid'),
		('failed', 'Failed'),
	]

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	currency = models.CharField(max_length=10, default='INR')
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
	razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
	razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
	razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('-created_at',)

	def mark_paid(self, payment_id, signature):
		self.status = 'paid'
		self.razorpay_payment_id = payment_id
		self.razorpay_signature = signature
		self.save()

	def mark_failed(self):
		self.status = 'failed'
		self.save()

