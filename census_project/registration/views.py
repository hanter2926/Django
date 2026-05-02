from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail  # Import add kiya
from .forms import CitizenForm
import random
import time

def register_citizen(request):
    form = CitizenForm() 
    if request.method == 'POST':
        form = CitizenForm(request.POST)
        if form.is_valid():
            if request.session.get('is_phone_verified'):
                form.save()
                messages.success(request, "Registration Successful!")
                del request.session['is_phone_verified']
                return redirect('register')
            else:
                messages.error(request, "Please verify your email first!")
    
    return render(request, 'registration/form.html', {'form': form})
def send_otp_view(request):
    if request.method == 'POST':
        user_email = request.POST.get('email') 
        otp = random.randint(100000, 999999)
        
        send_mail(
            'Bharat Jan-Sankhya Registration OTP',
            f'Aapka OTP hai: {otp}',
            'vk3288129@gmail.com',
            [user_email], # Yahan user_email hona chahiye
            fail_silently=False,
        )
        
        request.session['otp'] = otp
        request.session['otp_time'] = time.time()
        print(f"OTP generated: {otp}") 
        return redirect('verify_otp')
    return render(request, 'registration/send_otp.html')
def verify_otp_view(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        saved_otp = request.session.get('otp')
        saved_time = request.session.get('otp_time')
        
        if saved_otp and (time.time() - saved_time) < 180:
            if str(user_otp) == str(saved_otp):
                request.session['is_phone_verified'] = True
                messages.success(request, "OTP Verified Successfully!")
                return redirect('register')
            else:
                messages.error(request, "Invalid OTP!")
        else:
            messages.error(request, "OTP Expired! Please try again.")
            
    return render(request, 'registration/verify_otp.html')