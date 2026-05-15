from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Profile, Story, Message
from .forms import ProductForm, RegisterForm, UserUpdateForm, ProfileUpdateForm

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.db.models import Q

from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings

import random

# --- PRODUCT VIEWS ---

# Product List (Ab yahan seller aur created_at ke hisab se dikhega)
def product_list(request):
    products = Product.objects.all().order_by('-created_at')
    return render(
        request,
        'products/product_list.html',
        {'products': products}
    )

# Create Product (Yahan 'seller' use kiya gaya hai)
@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user  # 'user' ki jagah 'seller'
            product.save()
            messages.success(request, "Product added successfully!")
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'products/product_form.html', {'form': form})

# Edit Product
@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Check karein ki edit karne wala seller hi hai
    if product.seller != request.user:
        messages.error(request, "You are not authorized to edit this.")
        return redirect('product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'products/product_form.html', {'form': form})

# Delete Product
@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if product.seller == request.user:
        product.delete()
        messages.success(request, "Product deleted!")
    return redirect('product_list')


# --- WHATSAPP STYLE FEATURES ---

# Profile View (DP aur Bio dikhane ke liye)
@login_required
def profile_view(request):
    user_stories = Story.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'management/profile.html', {'stories': user_stories})

# Profile Settings (WhatsApp ki tarah DP badalne ke liye)
@login_required
def profile_settings(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Profile updated!")
            return redirect('profile_settings')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {'u_form': u_form, 'p_form': p_form}
    return render(request, 'management/profile_settings.html', context)

# Story Upload
@login_required
def upload_story(request):
    if request.method == 'POST':
        image = request.FILES.get('story_image')
        if image:
            Story.objects.create(user=request.user, image=image)
            messages.success(request, "Story posted!")
            return redirect('product_list')
    return render(request, 'management/upload_story.html')

# Chat System
@login_required
def chat_view(request, receiver_id, product_id=None):
    receiver = get_object_or_404(User, id=receiver_id)
    product = get_object_or_404(Product, id=product_id) if product_id else None
    
    # Messages nikalna (WhatsApp style filter)
    messages_list = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=receiver)) |
        (Q(sender=receiver) & Q(receiver=request.user))
    ).order_by('timestamp')

    if request.method == 'POST':
        text = request.POST.get('message_text')
        if text:
            Message.objects.create(
                sender=request.user,
                receiver=receiver,
                product=product,
                text=text
            )
            return redirect(request.path_info)

    return render(request, 'management/chat.html', {
        'receiver': receiver,
        'messages_list': messages_list,
        'product': product
    })


# --- AUTHENTICATION ---

# Register
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        user = User.objects.create_user(username=username, email=email, password=password)
        otp = random.randint(100000, 999999)

        # OTP Email (Development ke liye console backend use karein)
        send_mail(
            'Your Verification Code',
            f'Your OTP is: {otp}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=True,
        )

        request.session['otp'] = otp
        request.session['email'] = email
        return redirect('verify_otp')

    return render(request, 'registration/register.html')

# Verify OTP
def verify_otp(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        session_otp = request.session.get('otp')

        if str(user_otp) == str(session_otp):
            messages.success(request, "Account Verified!")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP")

    return render(request, 'registration/verify_otp.html')

# Logout
def custom_logout(request):
    logout(request)
    return redirect('/')