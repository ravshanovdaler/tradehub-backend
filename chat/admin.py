from django.contrib import admin
from .models import ChatRoom, ChatMessage

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 1

class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'seller', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('buyer__username', 'seller__username')
    inlines = [ChatMessageInline]

admin.site.register(ChatRoom, ChatRoomAdmin)
