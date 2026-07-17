from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CRMCalculation(models.Model):
    VALUE_TYPE_CHOICES = [
        ('PERCENTAGE', 'Percentage'),
        ('USD', 'USD'),
        ('UZS', 'UZS'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crm_calculations')
    name = models.CharField(max_length=100)
    value_type = models.CharField(max_length=15, choices=VALUE_TYPE_CHOICES, default='PERCENTAGE')
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # stores either percentage rate or flat USD value
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        symbol = "%" if self.value_type == 'PERCENTAGE' else " USD"
        return f"{self.user.username} - {self.name} ({self.value}{symbol})"
