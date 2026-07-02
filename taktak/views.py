import random

import razorpay
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify
from .catalog import discover_catalog
from .forms import ContactForm, CustomUserCreationForm, OTPVerificationForm, ProfileUpdateForm, SellProductForm, UserForm
from .models import Category, ContactMessage, GalleryImage, Order, OrderItem, Product, Review, TeamMember, UserProfile


def get_catalog_item(category_slug, product_slug):
    for category in discover_catalog():
        if category['slug'] == category_slug:
            for product in category['products']:
                if product['slug'] == product_slug:
                    return category, product
    return None, None


def home(request):
    catalog = discover_catalog()
    return render(request, 'taktak/home.html', {'catalog': catalog})


def product_list(request):
    catalog = discover_catalog()
    query = request.GET.get('q', '').strip()

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related('category').order_by('-created_at')
        return render(request, 'taktak/products.html', {
            'catalog': catalog,
            'products': products,
            'search_query': query,
            'show_search_results': True,
        })

    return render(request, 'taktak/products.html', {'catalog': catalog})


def category_products(request, slug):
    catalog = discover_catalog()
    selected_category = None
    for category in catalog:
        if category['slug'] == slug:
            selected_category = category
            break
    return render(request, 'taktak/products.html', {'catalog': catalog, 'selected_category': selected_category})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    reviews = product.reviews.select_related('user').all().order_by('-created_at')
    return render(request, 'taktak/product_detail.html', {'product': product, 'reviews': reviews})


def initiate_payment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed.'}, status=405)

    amount = request.POST.get('amount')
    order_id = request.POST.get('order_id')
    if not amount or not order_id:
        return JsonResponse({'error': 'Missing amount or order_id.'}, status=400)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    payment_order = client.order.create({
        'amount': int(float(amount) * 100),
        'currency': 'INR',
        'receipt': order_id,
        'payment_capture': 1,
    })

    order = get_object_or_404(Order, id=order_id)
    order.razorpay_order_id = payment_order['id']
    order.save(update_fields=['razorpay_order_id'])

    return JsonResponse({
        'success': True,
        'order_id': payment_order['id'],
        'amount': int(float(amount) * 100),
        'currency': 'INR',
        'key': settings.RAZORPAY_KEY_ID,
    })


def verify_payment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed.'}, status=405)

    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_signature = request.POST.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return JsonResponse({'error': 'Missing payment verification data.'}, status=400)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature,
    }

    try:
        client.utility.verify_payment_signature(params_dict)
        order = Order.objects.get(razorpay_order_id=razorpay_order_id)
        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature
        order.payment_status = 'Paid'
        order.status = 'Pending'
        order.save(update_fields=['razorpay_payment_id', 'razorpay_signature', 'payment_status', 'status'])
        return JsonResponse({'success': True, 'message': 'Payment verified successfully.'})
    except Exception:
        return JsonResponse({'success': False, 'message': 'Payment verification failed.'}, status=400)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            otp = f"{random.randint(100000, 999999)}"
            request.session['signup_data'] = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'phone': form.cleaned_data['phone'],
                'password': form.cleaned_data['password1'],
            }
            request.session['signup_otp'] = otp
            request.session['signup_email'] = form.cleaned_data['email']
            send_mail(
                'Your OTP for Taktak registration',
                f'Your OTP is {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [form.cleaned_data['email']],
                fail_silently=True,
            )
            messages.success(request, 'OTP has been sent to your email. Please verify it to complete registration.')
            return redirect('verify_otp')
    else:
        form = CustomUserCreationForm()
    return render(request, 'taktak/register.html', {'form': form})


def verify_otp(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            if otp == request.session.get('signup_otp'):
                signup_data = request.session.get('signup_data')
                if signup_data:
                    user = get_user_model().objects.create_user(
                        username=signup_data['username'],
                        email=signup_data['email'],
                        password=signup_data['password'],
                    )
                    user.save()
                    user = authenticate(username=signup_data['username'], password=signup_data['password'])
                    if user is not None:
                        login(request, user)
                        request.session.pop('signup_data', None)
                        request.session.pop('signup_otp', None)
                        request.session.pop('signup_email', None)
                        messages.success(request, 'Registration complete! You are now logged in.')
                        return redirect('home')
            messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    return render(request, 'taktak/verify_otp.html', {'form': form})


def about_us(request):
    team_members = TeamMember.objects.all()
    return render(request, 'taktak/about_us.html', {'team_members': team_members})


def gallery(request):
    images = GalleryImage.objects.all().order_by('-created_at')
    return render(request, 'taktak/gallery.html', {'images': images})


def product_gallery(request):
    products = Product.objects.select_related('category').all().order_by('-created_at')
    return render(request, 'taktak/product_gallery.html', {'products': products})


def sell_product(request):
    if request.method == 'POST':
        form = SellProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            base_slug = slugify(product.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            product.slug = slug
            product.save()
            messages.success(request, 'Your product has been listed for sale.')
            return redirect('product_list')
    else:
        form = SellProductForm()
    return render(request, 'taktak/sell_product.html', {'form': form})


def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message was sent successfully.')
            return redirect('contact_us')
    else:
        form = ContactForm()
    return render(request, 'taktak/contact_us.html', {'form': form})


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'taktak/profile.html', {'profile': profile_obj})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'taktak/my_orders.html', {'orders': orders})


@login_required
def razorpay_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'taktak/razorpay_payment.html', {
        'order': order,
        'razorpay_api_key': settings.RAZORPAY_API_KEY,
        'amount': int(order.total * 100),
    })


@login_required
def verify_razorpay_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.payment_status = 'Paid'
    order.status = 'Pending'
    order.save(update_fields=['payment_status', 'status'])
    messages.success(request, 'Razorpay payment completed successfully.')
    return redirect('my_orders')


@login_required
def submit_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        has_bought = OrderItem.objects.filter(order__user=request.user, order__payment_status='Paid', product=product).exists()
        if not has_bought:
            messages.error(request, 'You can only review products you bought.')
            return redirect('product_detail', slug=product.slug)
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '').strip()
        Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={'rating': rating, 'comment': comment},
        )
        messages.success(request, 'Your review has been saved.')
        return redirect('product_detail', slug=product.slug)
    return redirect('product_detail', slug=product.slug)


@login_required
def edit_profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile_obj)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was updated successfully.')
            return redirect('profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile_obj)
    return render(request, 'taktak/edit_profile.html', {'user_form': user_form, 'profile_form': profile_form})


def add_to_wishlist(request, slug):
    product = get_object_or_404(Product, slug=slug)
    wishlist = request.session.get('wishlist', [])
    if slug not in wishlist:
        wishlist.append(slug)
        request.session['wishlist'] = wishlist
        messages.success(request, f'{product.name} added to wishlist.')
    return redirect(request.META.get('HTTP_REFERER', reverse('product_list')))


def add_to_cart(request, category_slug, product_slug):
    category, product = get_catalog_item(category_slug, product_slug)
    if category is None or product is None:
        messages.error(request, 'The requested product could not be found.')
        return redirect('product_list')

    cart = request.session.get('cart', [])
    existing_item = next((item for item in cart if item['category_slug'] == category_slug and item['product_slug'] == product_slug), None)
    if existing_item:
        existing_item['quantity'] += 1
    else:
        cart.append({
            'category_slug': category_slug,
            'product_slug': product_slug,
            'name': product['name'],
            'price': float(product['price']),
            'image_url': product['images'][0] if product['images'] else '',
            'quantity': 1,
        })
    request.session['cart'] = cart
    messages.success(request, f'{product["name"]} added to cart.')
    return redirect(request.META.get('HTTP_REFERER', reverse('product_list')))


def cart_view(request):
    cart = request.session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render(request, 'taktak/cart.html', {'cart': cart, 'total': total})


def checkout(request):
    if request.method == 'POST':
        cart = request.session.get('cart', [])
        if not cart:
            messages.error(request, 'Your cart is empty.')
            return redirect('cart')

        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        payment_method = request.POST.get('payment_method')
        subtotal = sum(item['price'] * item['quantity'] for item in cart)
        delivery_charge = 5 if subtotal < 100 else 0
        tax = round(subtotal * 0.05, 2)
        total = round(subtotal + delivery_charge + tax, 2)
        items = ', '.join(f"{item['name']} x{item['quantity']}" for item in cart)
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=name,
            email=request.POST.get('email', 'noreply@example.com'),
            phone=phone,
            address=address,
            city=request.POST.get('city', 'N/A'),
            total=total,
            items=items,
            payment_status='Pending',
            status='Pending',
        )
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product_name=item['name'],
                product_slug=item.get('product_slug', ''),
                quantity=item['quantity'],
                price=item['price'],
            )
        request.session['cart'] = []
        send_mail(
            'Order confirmation - Taktak',
            f'Thank you for your purchase. Your order #{order.id} has been placed successfully.',
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            fail_silently=True,
        )

        if payment_method == 'razorpay':
            client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
            payment_order = client.order.create({
                'amount': int(total * 100),
                'currency': 'INR',
                'receipt': str(order.id),
                'payment_capture': 1,
            })
            order.razorpay_order_id = payment_order['id']
            order.save()

            context = {
                'order': order,
                'razorpay_order_id': payment_order['id'],
                'razorpay_api_key': settings.RAZORPAY_API_KEY,
                'amount': int(total * 100),
            }
            return render(request, 'taktak/razorpay_payment.html', context)

        else: # For 'cod' or other methods
            request.session['cart'] = []
            messages.success(request, 'Order placed successfully.')
            return redirect('my_orders')

    selected_category_slug = request.GET.get('category')
    selected_product_slug = request.GET.get('product')
    cart = request.session.get('cart', [])
    if selected_category_slug and selected_product_slug:
        category, product = get_catalog_item(selected_category_slug, selected_product_slug)
        if category and product:
            cart = [{
                'category_slug': selected_category_slug,
                'product_slug': selected_product_slug,
                'name': product['name'],
                'price': float(product['price']),
                'image_url': product['images'][0] if product['images'] else '',
                'quantity': 1,
            }]
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    delivery_charge = 5 if subtotal < 100 else 0
    tax = round(subtotal * 0.05, 2)
    total = round(subtotal + delivery_charge + tax, 2)
    context = {
        'cart': cart,
        'subtotal': subtotal,
        'delivery_charge': delivery_charge,
        'tax': tax,
        'total': total,
        'razorpay_api_key': settings.RAZORPAY_API_KEY
    }
    return render(request, 'taktak/checkout.html', context)


def privacy_policy(request):
    return render(request, 'taktak/privacy_policy.html')


def refund_policy(request):
    return render(request, 'taktak/refund_policy.html')


def shipping_policy(request):
    return render(request, 'taktak/shipping_policy.html')


def terms_and_conditions(request):
    return render(request, 'taktak/terms_and_conditions.html')


def mission(request):
    return render(request, 'taktak/mission.html')


def vision(request):
    return render(request, 'taktak/vision.html')
