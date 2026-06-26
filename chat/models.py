from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatRoom(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_chatrooms')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_chatrooms')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('buyer', 'seller')

    def __str__(self):
        return f"Chat: {self.buyer.username} & {self.seller.username}"

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Msg from {self.sender.username} at {self.timestamp}"
