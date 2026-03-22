from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from .models import Transaction, Notification, BudgetDetail
from django.utils import timezone
from decimal import Decimal

@receiver(post_save, sender=Transaction)
def check_budget_limit(sender, instance, created, **kwargs):
    if instance.category and not instance.is_income:
        plan_details = BudgetDetail.objects.filter(
            category=instance.category,
            budget__month=instance.date.month,
            budget__year=instance.date.year,
            plan_type='egreso'
        )
        if not plan_details.exists():
            return
            
        planned_amount = plan_details.aggregate(t=Sum('total_amount'))['t'] or Decimal('0.0')
            
        spent_obj = Transaction.objects.filter(
            category=instance.category,
            date__month=instance.date.month,
            date__year=instance.date.year,
            is_income=False
        ).aggregate(total=Sum('amount'))
        
        spent = spent_obj['total'] or Decimal('0.0')
        
        if planned_amount > 0:
            percentage = (spent / planned_amount) * 100
            
            if percentage >= 100:
                Notification.objects.create(message=f"Alerta: Has superado el 100% del presupuesto para {instance.category.name} (${spent} de ${planned_amount}).")
            elif percentage >= 80:
                Notification.objects.create(message=f"Aviso: Has consumido el {percentage:.1f}% de tu presupuesto para {instance.category.name}.")
