from django.shortcuts import render, redirect
from .models import Announcement
from .models import TeamMember
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth import authenticate, login
from django.db.models import Q
import random
from django.core.mail import send_mail
from django.conf import settings



def about(request):

    team=TeamMember.objects.all()

    context={
        'team':team
    }

    return render(request,'about.html',context)

def home(request):

    announcement = Announcement.objects.filter(active=True).first()

    return render(request,
                  "home.html",
                  {"announcement": announcement})

from .models import Gallery

def gallery(request):

    images=Gallery.objects.all()

    return render(request,'gallery.html',{'images':images})

def privacy_policy(request):
    return render(request, "privacy_policy.html")

def refund_policy(request):
    return render(request, "refund_policy.html")

def shipping_policy(request):
    return render(request, "shipping_policy.html")

def terms_conditions(request):
    return render(request, "terms_conditions.html")

def our_mission(request):
    return render(request, "our_mission.html")

def our_vision(request):
    return render(request, "our_vision.html")

def contact(request):
    return render(request, "contact.html")

import random
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile

def register_view(request):
    if request.method == 'POST':
        u_name = request.POST['username']
        email = request.POST['email']
        mobile = request.POST['mobile']
        pass1 = request.POST['password']
        
        if User.objects.filter(username=u_name).exists():
            messages.error(request, "Username pehle se maujood hai!")
            return redirect('register')
        if UserProfile.objects.filter(mobile_number=mobile).exists():
            messages.error(request, "Mobile Number pehle se registered hai!")
            return redirect('register')
            
        # 1. User ko abhi ke liye Inactive banayein jab tak OTP verify na ho
        new_user = User.objects.create_user(username=u_name, email=email, password=pass1)
        new_user.is_active = False 
        new_user.save()
        
        # 2. OTP Generate karein
        otp = str(random.randint(100000, 999999))
        
        profile = UserProfile.objects.create(user=new_user, mobile_number=mobile, otp=otp)
        profile.save()
        
        # 3. SMTP Ke Zariye Asli Email Bhejna
        try:
            subject = "Taktak App - Verify Your Account"
            message = f"Hello {u_name},\n\nAapka registration OTP hai: {otp}\n\nKripya account active karne ke liye ise enter karein."
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]
            
            send_mail(subject, message, from_email, recipient_list)
            messages.success(request, "Aapke Email par OTP bhej diya gaya hai!")
        except Exception as e:
            # Agar SMTP setup nahi hai toh testing ke liye terminal par print hoga
            print(f"🔥 SMTP ERROR: Mail nahi gaya. TESTING OTP IS: {otp}")
            messages.warning(request, "Email nahi ja saka, lekin testing OTP terminal par check karein!")

        # 4. REDIRECT: Ab user login par nahi balki OTP page par jayega
        request.session['register_user_id'] = new_user.id
        return redirect('verify_register_otp')
        
    return render(request, 'register.html')


def verify_register_otp(request):
    user_id = request.session.get('register_user_id')
    if not user_id:
        return redirect('register')
        
    if request.method == 'POST':
        entered_otp = request.POST['otp']
        
        try:
            user = User.objects.get(id=user_id)
            user_profile = UserProfile.objects.get(user=user)
            
            if user_profile.otp == entered_otp:
                user.is_active = True # Account ko active kar diya!
                user.save()
                
                user_profile.otp = None # OTP use ho gaya toh clear kar diya
                user_profile.save()
                
                del request.session['register_user_id']
                messages.success(request, "Account verify ho gaya! Ab aap login kar sakte hain.")
                return redirect('login')
            else:
                messages.error(request, "Galat OTP! Kripya fir se dekh kar dalein.")
        except User.DoesNotExist:
            return redirect('register')
            
    return render(request, 'verify_register_otp.html')

def login_view(request):
    if request.method == 'POST':
        # `.get()` use karne se KeyError KABHI nahi aayega!
        login_input = request.POST.get('login_input')
        pass1 = request.POST.get('password')
        
        # AGAR user ke form mein 'login_input' nahi hai, toh purana 'username' pakdo
        if not login_input:
            login_input = request.POST.get('username') or request.POST.get('email') or request.POST.get('mobile')

        user = None
        
        # 1. Check karein agar input Email hai ya Username hai
        user_queryset = User.objects.filter(Q(username=login_input) | Q(email=login_input))
        
        if user_queryset.exists():
            user_obj = user_queryset.first()
            user = authenticate(username=user_obj.username, password=pass1)
        else:
            # 2. Check karein agar input Mobile Number hai
            profile_queryset = UserProfile.objects.filter(mobile_number=login_input)
            if profile_queryset.exists():
                user_obj = profile_queryset.first().user
                user = authenticate(username=user_obj.username, password=pass1)
                
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Galat Details! Kripya fir se koshish karein.")
            
    return render(request, 'login.html')

def forget_password(request):
    if request.method == 'POST':
        login_input = request.POST['login_input']
        
        # User dhoodhna unke email, username ya mobile se
        user_profile = None
        user_obj = User.objects.filter(Q(username=login_input) | Q(email=login_input)).first()
        
        if user_obj:
            user_profile = UserProfile.objects.filter(user=user_obj).first()
        else:
            user_profile = UserProfile.objects.filter(mobile_number=login_input).first()
            
        if user_profile:
            # Live OTP Generate karna (6-digit)
            otp = str(random.randint(100000, 999999))
            user_profile.otp = otp
            user_profile.save()
            
            # Aapke terminal par OTP print hoga (Testing ke liye)
            print(f"🔥 LIVE OTP FOR {user_profile.user.username} IS: {otp}")
            
            # Session mein user id save kar rahe hain taaki agle page par use kar sakein
            request.session['reset_user_id'] = user_profile.user.id
            messages.success(request, f"OTP generate ho gaya hai! (Terminal check karein: {otp})")
            return redirect('verify_otp')
        else:
            messages.error(request, "Aisa koi user nahi mila!")
            
    return render(request, 'forget_password.html')


def verify_otp(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('forget_password')
        
    if request.method == 'POST':
        entered_otp = request.POST['otp']
        new_password = request.POST['new_password']
        
        user = User.objects.get(id=user_id)
        user_profile = UserProfile.objects.get(user=user)
        
        if user_profile.otp == entered_otp:
            # Password badalna
            user.set_password(new_password)
            user.save()
            
            # OTP khali karna taaki dubara use na ho
            user_profile.otp = None
            user_profile.save()
            
            del request.session['reset_user_id'] # Session clear
            messages.success(request, "Password successfully badal gaya hai! Ab login karein.")
            return redirect('login')
        else:
            messages.error(request, "Galat OTP! Kripya sahi OTP dalein.")
            
    return render(request, 'verify_otp.html')