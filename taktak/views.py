import random
from datetime import timedelta

import razorpay
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from .catalog import discover_catalog
from .forms import ContactForm, CustomUserCreationForm, OTPVerificationForm, ProfileUpdateForm, SellProductForm, UserForm
from .models import Category, ContactMessage, GalleryImage, Order, OrderItem, Product, Review, SystemLog, StockHistoryLog, TeamMember, UserProfile


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

    client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
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
        'key': settings.RAZORPAY_API_KEY,
    })


def verify_payment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed.'}, status=405)

    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_signature = request.POST.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return JsonResponse({'error': 'Missing payment verification data.'}, status=400)

    client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
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


def signup_view(request):
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


def verify_otp_and_register(request):
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
                    UserProfile.objects.create(user=user)
                    user = authenticate(username=signup_data['username'], password=signup_data['password'])
                    if user is not None:
                        login(request, user)
                        request.session.pop('signup_data', None)
                        request.session.pop('signup_otp', None)
                        request.session.pop('signup_email', None)

                        # Send Welcome Email
                        subject = 'Welcome to Taktak!'
                        html_message = render_to_string(
                            'taktak/emails/welcome_email.html',
                            {'username': user.username}
                        )
                        send_mail(
                            subject,
                            '', # Plain text message (optional)
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                            fail_silently=False,
                            html_message=html_message)
                        messages.success(request, 'Registration complete! You are now logged in.')
                        return redirect('home')
            messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    return render(request, 'taktak/verify_otp.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        from django.contrib.auth.forms import AuthenticationForm
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                UserProfile.objects.get_or_create(user=user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect('profile')
            else:
                messages.error(request,"Invalid username or password.")
    form = AuthenticationForm()
    return render(request, 'taktak/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('home')

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
def profile_view(request):
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
def edit_profile_view(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile_obj)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was updated successfully.')
            return redirect('profile_view')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile_obj)
    return render(request, 'taktak/edit_profile.html', {'user_form': user_form, 'profile_form': profile_form})


@login_required
def reject_or_switch_order(request, order_id):
    """
    Allows an assigned seller to reject an order, triggering a switch to the next
    closest seller.
    """
    order = get_object_or_404(Order, id=order_id)
    messages.error(request, "Seller rejection flow is currently unavailable.")
    return redirect('home')

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

    db_product = get_object_or_404(Product, slug=product_slug)
    if db_product.is_out_of_stock:
        messages.error(request, 'This product is currently out of stock.')
        return redirect(request.META.get('HTTP_REFERER', reverse('product_list')))

    cart = request.session.get('cart', [])
    existing_item = next((item for item in cart if item['product_slug'] == product_slug), None)

    item_data = {
        'category_slug': category_slug,
        'product_slug': product_slug,
        'name': db_product.name,
        'original_price': float(db_product.original_price),
        'price': float(db_product.discounted_price),
        'discount_percentage': db_product.discount_percentage,
        'savings': float(db_product.savings_amount),
        'image_url': db_product.display_image_url,
        'quantity': 1,
        'sku_number': db_product.sku_number,
        'stock': db_product.stock,
    }

    if existing_item:
        if existing_item['quantity'] < db_product.stock:
            existing_item['quantity'] += 1
        else:
            messages.error(request, 'You have reached the maximum available stock for this product.')
            return redirect(request.META.get('HTTP_REFERER', reverse('product_list')))
    else:
        cart.append(item_data)

    request.session['cart'] = cart
    messages.success(request, f'{db_product.name} added to cart.')
    return redirect(request.META.get('HTTP_REFERER', reverse('product_list')))


def cart_view(request):
    cart = request.session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    subtotal = sum(item.get('original_price', item['price']) * item['quantity'] for item in cart)
    return render(request, 'taktak/cart.html', {'cart': cart, 'total': total, 'subtotal': subtotal})


def checkout(request):
    cart = request.session.get('cart', [])
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    delivery_charge = 5 if subtotal < 100 else 0
    tax = round(subtotal * 0.05, 2)
    total = round(subtotal + delivery_charge + tax, 2)
    amount_in_cents = int(total * 100)
    default_delivery_date = (timezone.now().date() + timedelta(days=5)).isoformat()
    out_of_stock_items = [item for item in cart if item.get('stock', 1) == 0]
    has_out_of_stock = bool(out_of_stock_items)

    if request.method == 'POST':
        if has_out_of_stock:
            messages.error(request, 'One or more items in your cart are out of stock and cannot be ordered.')
            return render(request, 'taktak/checkout.html', {
                'cart': cart,
                'subtotal': subtotal,
                'delivery_charge': delivery_charge,
                'tax': tax,
                'total': total,
                'default_delivery_date': default_delivery_date,
                'razorpay_api_key': settings.RAZORPAY_API_KEY,
                'amount': amount_in_cents,
                'razorpay_order_id': None,
                'out_of_stock_items': out_of_stock_items,
                'has_out_of_stock': has_out_of_stock,
            })

        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        payment_method = request.POST.get('payment_method')
        delivery_date = request.POST.get('delivery_date')
        delivery_location = request.POST.get('delivery_location')

        if not all([name, email, phone, address, city, payment_method]):
            messages.error(request, 'Please fill out all required fields.')
            return redirect('checkout')

        items_summary = ', '.join(f"{item['name']} x{item['quantity']}" for item in cart)

        insufficient_items = []
        validated_items = []
        for item in cart:
            product_slug = item.get('product_slug', '')
            if not product_slug:
                insufficient_items.append(item['name'])
                continue

            try:
                product_instance = Product.objects.get(slug=product_slug)
            except Product.DoesNotExist:
                product_instance = None

            if not product_instance or product_instance.stock < item['quantity']:
                insufficient_items.append(item['name'])
                continue

            validated_items.append((item, product_instance))

        if insufficient_items:
            messages.error(request, 'One or more cart items are no longer available in the requested quantity.')
            return render(request, 'taktak/checkout.html', {
                'cart': cart,
                'subtotal': subtotal,
                'delivery_charge': delivery_charge,
                'tax': tax,
                'total': total,
                'default_delivery_date': default_delivery_date,
                'razorpay_api_key': settings.RAZORPAY_API_KEY,
                'amount': amount_in_cents,
                'razorpay_order_id': None,
                'out_of_stock_items': out_of_stock_items,
                'has_out_of_stock': has_out_of_stock,
            })

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            total=total,
            items=items_summary,
            payment_method=payment_method,
            payment_status='Pending',
            status='Pending',
            delivery_location=delivery_location or address,
            delivery_date=delivery_date or timezone.now().date() + timedelta(days=5),
        )

        for item, product_instance in validated_items:
            OrderItem.objects.create(
                order=order,
                product=product_instance,
                product_name=item['name'],
                product_slug=item['product_slug'],
                quantity=item['quantity'],
                price=item['price'],
            )

        SystemLog.objects.create(
            order=order,
            event_type='Order created',
            details=f'Order created with {len(validated_items)} item(s). Subtotal: {subtotal:.2f}, Total: {total:.2f}.',
            created_by=request.user if request.user.is_authenticated else None,
        )

        for item, product_instance in validated_items:
            original_stock, new_stock = product_instance.adjust_stock(-item['quantity'], user=request.user if request.user.is_authenticated else None, note='Order placed and stock decremented.')
            SystemLog.objects.create(
                order=order,
                event_type='Stock updated',
                details=f'Stock for {product_instance.name} decreased from {original_stock} to {new_stock}.',
                created_by=request.user if request.user.is_authenticated else None,
            )
            if new_stock <= product_instance.low_stock_threshold:
                SystemLog.objects.create(
                    order=order,
                    event_type='Critical stock alert',
                    details=f'{product_instance.name} stock reached {new_stock}, below threshold {product_instance.low_stock_threshold}.',
                    created_by=request.user if request.user.is_authenticated else None,
                )

        if payment_method == 'razorpay':
            try:
                client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
                payment_order = client.order.create({
                    'amount': amount_in_cents,
                    'currency': 'INR',
                    'receipt': str(order.id),
                    'payment_capture': 1,
                })
                order.razorpay_order_id = payment_order['id']
                order.save(update_fields=['razorpay_order_id'])

                request.session['cart'] = []
                messages.success(request, 'Your order has been placed. Please complete the payment.')

                context = {
                    'order': order,
                    'razorpay_order_id': payment_order['id'],
                    'razorpay_api_key': settings.RAZORPAY_API_KEY,
                    'amount': amount_in_cents,
                }
                return render(request, 'taktak/razorpay_payment.html', context)
            except Exception as e:
                messages.error(request, f'Could not initiate Razorpay payment. Error: {e}')
                order.delete()
                return redirect('checkout')

        request.session['cart'] = []
        send_mail(
            'Order confirmation - Taktak',
            f'Thank you for your purchase. Your order #{order.id} has been placed successfully.',
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            fail_silently=True,
        )
        messages.success(request, 'Order placed successfully.')
        return redirect('my_orders')

    context = {
        'cart': cart,
        'subtotal': subtotal,
        'delivery_charge': delivery_charge,
        'tax': tax,
        'total': total,
        'default_delivery_date': default_delivery_date,
        'razorpay_api_key': settings.RAZORPAY_API_KEY,
        'amount': amount_in_cents,
        'razorpay_order_id': None,
        'out_of_stock_items': out_of_stock_items,
        'has_out_of_stock': has_out_of_stock,
    }
    return render(request, 'taktak/checkout.html', context)


@login_required
def order_tracking(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        if 'change_date' in request.POST:
            requested_date = request.POST.get('requested_delivery_date')
            if requested_date:
                order.date_change_requested = True
                order.requested_delivery_date = requested_date
                order.save(update_fields=['date_change_requested', 'requested_delivery_date'])
                SystemLog.objects.create(
                    order=order,
                    event_type='Delivery date change requested',
                    details=f'User requested new delivery date: {requested_date}.',
                    created_by=request.user,
                )
                messages.success(request, 'Your delivery date change request has been submitted.')
                return redirect('order_tracking', order_id=order.id)

        if 'change_location' in request.POST:
            requested_location = request.POST.get('requested_delivery_location')
            if requested_location:
                order.location_change_requested = True
                order.requested_delivery_location = requested_location
                order.save(update_fields=['location_change_requested', 'requested_delivery_location'])
                SystemLog.objects.create(
                    order=order,
                    event_type='Delivery location change requested',
                    details=f'User requested new delivery location: {requested_location}.',
                    created_by=request.user,
                )
                messages.success(request, 'Your delivery reroute request has been submitted.')
                return redirect('order_tracking', order_id=order.id)

    arrival_date = order.delivery_date
    progress = ['Processed', 'Transit', 'Delivered']
    current_step = progress.index(order.tracking_state) if order.tracking_state in progress else 0

    context = {
        'order': order,
        'arrival_date': arrival_date,
        'progress': progress,
        'current_step': current_step,
        'progress_percent': ((current_step + 1) / len(progress)) * 100,
    }
    return render(request, 'taktak/order_tracking.html', context)


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
