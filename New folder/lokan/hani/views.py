from django.shortcuts import render
from .models import Product

def home_page(request):
    # Separate the query to specifically grab checked "Top Products"
    top_products = Product.objects.filter(top_product=True)
    all_products = Product.objects.all()

    context = {
        'top_products': top_products,
        'all_products': all_products
    }
    return render(request, 'home.html', context)