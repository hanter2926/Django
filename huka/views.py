from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import UserProfile, ChatMessage, Friendship
from django.db.models import Q
import json

# ==========================================
# 1. AUTH SYSTEM VIEWS
# ==========================================

# Register View
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # User bante hi uski Candy Crush Profile bhi auto-create ho jayegi
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('game_home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

# Login View
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('game_home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# Logout View
def logout_view(request):
    logout(request)
    return redirect('login')


# ==========================================
# 2. GAME LOGIC VIEWS
# ==========================================

# Main Game View (Sirf Logged-In Users khel payenge)
@login_required(login_url='login')
def game_home(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    context = {
        'level': profile.current_level,
        'coins': profile.total_coins,
        'username': request.user.username
    }
    return render(request, 'index.html', context)

# Level Complete API (Jab JavaScript se request aayegi)
@login_required
def complete_level_api(request):
    if request.method == 'POST':
        profile = request.user.profile
        success = profile.complete_level()
        if success:
            return JsonResponse({
                'status': 'success',
                'new_level': profile.current_level,
                'new_coins': profile.total_coins,
                'message': 'Badhai ho! +15 Coins mile.'
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Aap pehle hi Max Level 100 par hain!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid Request'})


# ==========================================
# 3. SOCIAL SYSTEM VIEWS
# ==========================================

# Social Dashboard View (Sabhi players aur requests dekhne ke liye)
@login_required
def social_dashboard(request):
    current_user = request.user
    
    # Un logo ki list jinhe request bheji ja chuki hai ya jinhone bheji hai
    already_connected = Friendship.objects.filter(Q(sender=current_user) | Q(receiver=current_user))
    connected_users_ids = []
    for f in already_connected:
        connected_users_ids.append(f.sender.id)
        connected_users_ids.append(f.receiver.id)
    
    # Baaki bache huye players
    other_players = User.objects.exclude(id__in=connected_users_ids).exclude(id=current_user.id)
    
    # Aayi hui Pending Requests
    pending_requests = Friendship.objects.filter(receiver=current_user, status='pending')
    
    # Aapke Friends (Jahan status 'accepted' ho)
    friends_connections = Friendship.objects.filter(
        Q(sender=current_user) | Q(receiver=current_user), status='accepted'
    )
    friends = []
    for conn in friends_connections:
        if conn.sender == current_user:
            friends.append(conn.receiver)
        else:
            friends.append(conn.sender)

    context = {
        'other_players': other_players,
        'pending_requests': pending_requests,
        'friends': friends
    }
    return render(request, 'social.html', context)

# Friend Request Bhejne ki API
@login_required
def send_friend_request(request, user_id):
    receiver = User.objects.get(id=user_id)
    Friendship.objects.get_or_create(sender=request.user, receiver=receiver, status='pending')
    return redirect('social_dashboard')

# Friend Request Accept Karne ki API
@login_required
def accept_friend_request(request, request_id):
    friend_request = Friendship.objects.get(id=request_id, receiver=request.user)
    friend_request.status = 'accepted'
    friend_request.save()
    return redirect('social_dashboard')

# Friend Request Reject/Cancel Karne ki API
@login_required
def reject_friend_request(request, request_id):
    friend_request = Friendship.objects.get(id=request_id, receiver=request.user)
    friend_request.delete()
    return redirect('social_dashboard')


# ==========================================
# 4. REAL-TIME CHAT VIEWS
# ==========================================

# Main Chat Page View
@login_required
def chat_room(request, friend_id):
    friend = User.objects.get(id=friend_id)
    # Fixed: Changed models.Q to Q and .ordering() to .order_by()
    messages = ChatMessage.objects.filter(
        (Q(sender=request.user) & Q(receiver=friend)) |
        (Q(sender=friend) & Q(receiver=request.user))
    ).order_by('timestamp')
    
    return render(request, 'chat.html', {'friend': friend, 'old_messages': messages})

# Message Send/Fetch karne ki API
@login_required
def send_and_get_messages_api(request, friend_id):
    friend = User.objects.get(id=friend_id)
    
    # CASE 1: Agar message send karne ke liye POST request aayi hai
    if request.method == 'POST':
        data = json.loads(request.body)
        msg_text = data.get('message_text')
        if msg_text:
            ChatMessage.objects.create(sender=request.user, receiver=friend, message_text=msg_text)
            return JsonResponse({'status': 'sent'})
            
    # CASE 2: Naye messages fetch karne ke liye GET request
    # Fixed: Changed models.Q to Q and .ordering() to .order_by()
    messages = ChatMessage.objects.filter(
        (Q(sender=request.user) & Q(receiver=friend)) |
        (Q(sender=friend) & Q(receiver=request.user))
    ).order_by('timestamp')
    
    messages_list = []
    for m in messages:
        messages_list.append({
            'sender': m.sender.username,
            'text': m.message_text,
            'time': m.timestamp.strftime('%H:%M')
        })
        
    return JsonResponse({'messages': messages_list, 'current_user': request.user.username})