from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from .forms import ProductForm, RegisterForm

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

from django.core.mail import send_mail


def product_list(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'products/product_list.html', {'products': products})


@login_required
def product_create(request):

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()

            return redirect('product_list')

    else:
        form = ProductForm()

    return render(request, 'products/product_form.html', {'form': form})


@login_required
def product_edit(request, pk):

    product = get_object_or_404(Product, pk=pk)

    if product.user != request.user:
        return redirect('product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():
            form.save()
            return redirect('product_list')

    else:
        form = ProductForm(instance=product)

    return render(request, 'products/product_form.html', {'form': form})


@login_required
def product_delete(request, pk):

    product = get_object_or_404(Product, pk=pk)

    if product.user == request.user:
        product.delete()

    return redirect('product_list')


def register(request):

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            # Welcome Email
            send_mail(
                'Welcome to Product App',
                f'Hello {user.username}, Welcome to our website!',
                'admin@gmail.com',
                [user.email],
                fail_silently=False,
            )

            login(request, user)

            return redirect('product_list')

    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})
