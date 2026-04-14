from django.shortcuts import render
from .models import Product  # Model import karna zaroori hai

def product_list(request):
    items = Product.objects.all()
    # 'myapp/index.html' ko hata kar sirf 'index.html' likhein
    return render(request, 'soping.html', {'items': items})