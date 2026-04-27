# from django.shortcuts import render
# from .models import Product

# def product_list(request):
#     products = Product.objects.all()
#     products_data = Product.objects.all()
#     return render(request, 'model.html',{'products': products})

#coppy

from django.shortcuts import render
from .models import Product

def product_list(request):
    products_data = Product.objects.all()
    
    return render(request, 'model.html', {
        'products': products_data
    })