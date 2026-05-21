from django.shortcuts import render, redirect
from .models import SupportMessage

def support_view(request):
    if request.method == "POST":
        SupportMessage.objects.create(
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            subject=request.POST.get('subject'),
            message=request.POST.get('message'),
        )
        return redirect('home')

    return render(request, 'support/support.html')
