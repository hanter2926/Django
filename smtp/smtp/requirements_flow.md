# E-Learning Platform Requirements Flow

## 1. Overview
Build an E-Learning backend and frontend using Django and DRF with support for:
- User roles: Admin, Instructor, Student
- Course and Lesson management
- Soft delete for content
- Image upload support via Cloudinary
- Payment flow using Razorpay
- Authentication via DRF Token and session login
- Pagination in both web UI and API

## 2. User Roles
- Admin: manage users, courses, lessons, payments, and review content.
- Instructor: create/update/delete courses and lessons, manage course content.
- Student: browse courses, view lessons, and access paid content.

## 3. Features
### Authentication
- Register with role selection
- Login via web form
- Token auth for API access
- Session auth for web pages

### Course Management
- CRUD operations for courses
- Soft delete courses and lessons
- Course image support via Cloudinary URLs
- Course listing with pagination

### Lessons
- Lesson CRUD per course
- Soft delete lessons
- Orderable lessons

### Payments
- Razorpay order creation for paid courses
- Payment verification endpoint
- Payment status tracking

### Search and Pagination
- Paginated course listing in web view
- API pagination using DRF page number pagination
- Optional search/filter fields for courses

## 4. Modules
- `tp.models`: User, Course, Lesson, soft delete.
- `tp.api`: DRF viewsets and auth endpoints.
- `tp.forms`: web registration and other forms.
- `tp.views`: web UI views and auth views.
- `tp.cloudinary_utils`: image upload helper.
- `tp.payments`: Razorpay integration.
- `tp.templates`: frontend pages for login/register, course/lesson pages.

## 5. System Workflow
1. User registers and logs in.
2. Instructor creates a course, optionally adding an image URL.
3. Students view paginated course list and course details.
4. Students can purchase paid courses via Razorpay if enabled.
5. Soft delete keeps data in database but hides it from regular views.
6. Admins can manage soft-deleted items from admin or via restore endpoints.

## 6. Implementation Notes
- Use `AUTH_USER_MODEL = 'tp.User'`.
- Use `objects = SoftDeleteManager()` and `all_objects` for hidden records.
- Use DRF `PageNumberPagination` and `paginate_by` for views.
- Use `cloudinary` package only when configured.
- Use `razorpay` package only when configured.

## 7. Next Enhancements
- Add course purchase history and enrollment model.
- Add lesson video uploads and streaming.
- Add role-based dashboard pages.
- Add email notifications for registration and payments.
