from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from .models import Transaction, Loan, IncomeSource, Budget, BudgetDetail, BudgetCategory, Entity, LoanType
from decimal import Decimal, InvalidOperation
import datetime

def clean_money_field(value):
    if not value and value != 0:
        return None
    if isinstance(value, str):
        val = value.replace('.', '').replace(',', '.')
        try:
            return Decimal(val)
        except InvalidOperation:
            raise forms.ValidationError("Monto numérico inválido")
    return Decimal(value)

def init_money_fields(form, fields_list):
    if form.instance and form.instance.pk:
        for f in fields_list:
            if f in form.fields:
                val = getattr(form.instance, f, None)
                if val is not None:
                    try:
                        val_str = f"{Decimal(str(val)):.2f}"
                        if val_str.endswith('.00'):
                            val_str = val_str[:-3]
                        elif '.' in val_str:
                            val_str = val_str.replace('.', ',')
                        form.initial[f] = val_str
                    except:
                        pass

class TransactionForm(forms.ModelForm):
    amount = forms.CharField(
        label='Monto ($)',
        widget=forms.TextInput(attrs={'class': 'money-input border-gray-300 rounded-lg shadow-sm w-full', 'placeholder': 'Ej: 15.000,50'})
    )

    class Meta:
        model = Transaction
        fields = ['date', 'description', 'amount', 'category', 'is_income']
        widgets = {
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }
        labels = {
            'date': 'Fecha',
            'description': 'Descripción',
            'category': 'Categoría',
            'is_income': '¿Es un Ingreso?'
        }
    
    def clean_amount(self):
        return clean_money_field(self.cleaned_data.get('amount'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_money_fields(self, ['amount'])

class LoanForm(forms.ModelForm):
    monthly_quota = forms.CharField(
        label='Valor Cuota Mensual ($)',
        widget=forms.TextInput(attrs={'class': 'money-input border-gray-300 rounded-lg shadow-sm w-full', 'placeholder': 'Ej: 347.773'})
    )

    class Meta:
        model = Loan
        fields = ['entity', 'loan_type', 'monthly_quota', 'total_quotas', 'remaining_quotas', 'start_date']
        widgets = {
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }
        labels = {
            'entity': 'Entidad / Banco',
            'loan_type': 'Tipo de Crédito',
            'total_quotas': 'Total de Cuotas',
            'remaining_quotas': 'Cuotas Restantes',
            'start_date': 'Fecha de Inicio'
        }

    def clean_monthly_quota(self):
        return clean_money_field(self.cleaned_data.get('monthly_quota'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_money_fields(self, ['monthly_quota'])

class IncomeSourceForm(forms.ModelForm):
    amount = forms.CharField(
        label='Monto Mensual ($)',
        widget=forms.TextInput(attrs={'class': 'money-input border-gray-300 rounded-lg shadow-sm w-full', 'placeholder': 'Ej: 2.600.000'})
    )

    class Meta:
        model = IncomeSource
        fields = ['entity', 'description', 'amount', 'is_fixed']
        labels = {
            'entity': 'Entidad / Empresa',
            'description': 'Descripción (Ej: Sueldo, Bono)',
            'is_fixed': '¿Es un ingreso fijo?'
        }

    def clean_amount(self):
        return clean_money_field(self.cleaned_data.get('amount'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_money_fields(self, ['amount'])

class BudgetForm(forms.ModelForm):
    MONTH_CHOICES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    
    month = forms.ChoiceField(choices=MONTH_CHOICES, label='Mes', widget=forms.Select(attrs={'class': 'border-gray-300 rounded-lg shadow-sm w-full'}))
    year = forms.ChoiceField(choices=[], label='Año', widget=forms.Select(attrs={'class': 'border-gray-300 rounded-lg shadow-sm w-full'}))

    total_budget = forms.CharField(
        label='Monto Total Asignado ($)',
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={'class': 'money-input border-gray-300 rounded-lg shadow-sm w-full bg-gray-100', 'readonly': 'readonly'})
    )

    class Meta:
        model = Budget
        fields = ['title', 'month', 'year', 'total_budget']
        labels = {
            'title': 'Título del Presupuesto (Ej: Marzo 2026)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_year = datetime.date.today().year
        self.fields['year'].choices = [(y, str(y)) for y in range(current_year, current_year + 11)]

class BudgetDetailForm(forms.ModelForm):
    amount = forms.CharField(
        label='Monto Unitario ($)',
        widget=forms.TextInput(attrs={'class': 'money-input border-gray-300 rounded-lg shadow-sm w-full', 'placeholder': 'Ej: 50.000'})
    )
    quantity = forms.CharField(
        label='Cantidad',
        required=False,
        widget=forms.TextInput(attrs={'class': 'money-input border-gray-300 rounded-lg shadow-sm w-full', 'placeholder': 'Ej: 1'})
    )

    class Meta:
        model = BudgetDetail
        fields = ['budget', 'plan_type', 'income_source', 'category', 'quantity', 'amount']
        labels = {
            'budget': 'Presupuesto Principal',
            'plan_type': 'Tipo de Flujo',
            'income_source': 'Fuente de Ingreso (Si es Ingreso)',
            'category': 'Categoría (Si es Egreso)'
        }

    def clean_amount(self):
        return clean_money_field(self.cleaned_data.get('amount'))
        
    def clean_quantity(self):
        val = self.cleaned_data.get('quantity')
        if not val: return Decimal('1')
        return clean_money_field(val)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_money_fields(self, ['amount', 'quantity'])

class BaseBudgetDetailFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        
        seen_ingresos = set()
        seen_egresos = set()
        
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            
            if not getattr(form, 'cleaned_data', None):
                continue
                
            ptype = form.cleaned_data.get('plan_type')
            if ptype == 'ingreso':
                src = form.cleaned_data.get('income_source')
                if src:
                    if src.id in seen_ingresos:
                        raise forms.ValidationError(f"El ingreso '{src}' está duplicado.")
                    seen_ingresos.add(src.id)
            elif ptype == 'egreso':
                cat = form.cleaned_data.get('category')
                if cat:
                    if cat.id in seen_egresos:
                        raise forms.ValidationError(f"La categoría '{cat}' está duplicada.")
                    seen_egresos.add(cat.id)

BudgetDetailFormSet = inlineformset_factory(
    Budget, BudgetDetail, form=BudgetDetailForm, formset=BaseBudgetDetailFormSet,
    extra=1, can_delete=True
)

class EntityForm(forms.ModelForm):
    class Meta:
        model = Entity
        fields = ['name']
        labels = {'name': 'Nombre de la Entidad / Banco'}

class LoanTypeForm(forms.ModelForm):
    class Meta:
        model = LoanType
        fields = ['name']
        labels = {'name': 'Tipo de Crédito'}

class BudgetCategoryForm(forms.ModelForm):
    class Meta:
        model = BudgetCategory
        fields = ['name', 'is_essential']
        labels = {
            'name': 'Nombre de Categoría',
            'is_essential': '¿Es un gasto esencial?'
        }
