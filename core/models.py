from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.contrib.auth.models import User
import re

def clp(value):
    if value is None: return '0'
    try:
        val = Decimal(str(value))
        val_str = f"{val:.2f}"
    except: return str(value)
    if val_str.endswith('.00'): val_str = val_str[:-3]
    else: val_str = val_str.replace('.', ',')
    parts = val_str.split(',')
    int_part = re.sub(r'\B(?=(\d{3})+(?!\d))', '.', parts[0])
    return f"{int_part},{parts[1]}" if len(parts) > 1 else int_part

class Entity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class LoanType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class IncomeSource(models.Model):
    """Registro de sueldos y ajustes (Ej: Imagemaker)"""
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, null=True)
    description = models.CharField(max_length=255) # Ej: Sueldo base, ajuste credito
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_fixed = models.BooleanField(default=True)
    created_at = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.entity} - {self.description} (${clp(self.amount)})"

class Loan(models.Model):
    """Motor de Créditos (Consumo, TDC, Hipotecario)"""
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, null=True)
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE, null=True)
    monthly_quota = models.DecimalField(max_digits=12, decimal_places=2)
    total_quotas = models.IntegerField()
    remaining_quotas = models.IntegerField()
    start_date = models.DateField()
    @property
    def end_date(self):
        """Calcula la fecha de término basada en cuotas restantes"""
        return self.start_date + relativedelta(months=self.total_quotas)

    @property
    def years_remaining(self):
        """Devuelve el equivalente en años (ej: 1.33)"""
        return round(self.remaining_quotas / 12, 2)

    def register_payment(self):
        if self.remaining_quotas > 0:
            self.remaining_quotas -= 1
            self.save()
            return True
        return False

    def __str__(self):
        ent_name = self.entity.name if self.entity else 'N/A'
        t_name = self.loan_type.name if self.loan_type else 'N/A'
        return f"{ent_name} - {t_name} (${clp(self.monthly_quota)}/mes)"

class BudgetCategory(models.Model):
    """Categorías: Comida, Gatos, Luz, etc."""
    name = models.CharField(max_length=100, unique=True)
    is_essential = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Notification(models.Model):
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.message

class Budget(models.Model):
    """Presupuesto Maestro (Cabecera)"""
    title = models.CharField(max_length=255)
    month = models.IntegerField() # 1-12
    year = models.IntegerField()
    created_at = models.DateField(auto_now_add=True)
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.title} ({self.month}/{self.year})"

    def update_totals(self):
        from django.db.models import Sum
        ingresos = self.details.filter(plan_type='ingreso').aggregate(t=Sum('total_amount'))['t'] or 0
        egresos = self.details.filter(plan_type='egreso').aggregate(t=Sum('total_amount'))['t'] or 0
        self.total_budget = ingresos - egresos
        self.save()

class BudgetDetail(models.Model):
    """Detalle del Presupuesto V4"""
    budget = models.ForeignKey(Budget, related_name='details', on_delete=models.CASCADE)
    
    PLAN_TYPE_CHOICES = [('ingreso', 'Ingreso'), ('egreso', 'Egreso')]
    plan_type = models.CharField(max_length=10, choices=PLAN_TYPE_CHOICES, default='egreso')
    
    income_source = models.ForeignKey(IncomeSource, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE, null=True, blank=True)
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.total_amount = self.amount * self.quantity
        super().save(*args, **kwargs)
        self.budget.update_totals()

    def delete(self, *args, **kwargs):
        budget = self.budget
        super().delete(*args, **kwargs)
        budget.update_totals()

    def __str__(self):
        sub = self.category.name if self.plan_type == 'egreso' and self.category else (
              self.income_source.description if self.income_source else 'N/A')
        return f"{self.budget.title} | {self.plan_type.capitalize()} - {sub} (${clp(self.total_amount)})"

class Transaction(models.Model):
    """Lo 'Real': Gastos e ingresos ejecutados diariamente"""
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(BudgetCategory, on_delete=models.SET_NULL, null=True)
    is_income = models.BooleanField(default=False)

    def __str__(self):
        type_t = "Ingreso" if self.is_income else "Gasto"
        return f"{self.date} - {type_t}: {self.description} (${clp(self.amount)})"
