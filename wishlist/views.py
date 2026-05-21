from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Wishlist
from products.models import Product


@login_required
def add_to_wishlist(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    return redirect('wishlist')


@login_required
def wishlist_view(request):

    wishlist_items = Wishlist.objects.filter(user=request.user)

    return render(request, 'wishlist/wishlist.html', {
        'wishlist_items': wishlist_items
    })


@login_required
def remove_wishlist(request, wishlist_id):

    item = get_object_or_404(Wishlist, id=wishlist_id)

    item.delete()

    return redirect('wishlist')
