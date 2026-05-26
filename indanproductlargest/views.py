from django.shortcuts import render

def promo_video(request):
    return render(request, 'ipl/promo.html')