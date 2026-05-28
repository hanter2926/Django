from django.contrib import admin
from .models import UserProfile, Friendship, ChatMessage

# 1. User Profile Admin (Coins aur Level dekhne ke liye)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_level', 'total_coins')
    search_fields = ('user__username',)
    list_filter = ('current_level',)

# 2. Friendship Admin (Dosti aur Status check karne ke liye)
@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('sender__username', 'receiver__username')

# 3. Chat Message Admin (Saare live chats monitor karne ke liye)
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'message_text', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'message_text')
    list_filter = ('timestamp',)