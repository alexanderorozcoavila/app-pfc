from django.http import JsonResponse
from django.views import View
from .models import IncomeSource, Loan, Transaction, BudgetCategory
from django.db.models import Sum
from decimal import Decimal
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.urls import reverse_lazy
import json
from django.utils import timezone
from .services import LoanSimulator
from .models import Transaction, Loan, IncomeSource, Budget, BudgetDetail, BudgetCategory, Entity, LoanType
from .forms import TransactionForm, LoanForm, IncomeSourceForm, BudgetForm, BudgetDetailForm, BudgetCategoryForm, EntityForm, LoanTypeForm

class MonthlyComparisonView(LoginRequiredMixin, View):
    def get(self, request, year, month):
        ingreso_total = IncomeSource.objects.aggregate(t=Sum('amount'))['t'] or Decimal('0.0')
        
        budget_total = BudgetPlan.objects.filter(year=year, month=month).aggregate(t=Sum('planned_amount'))['t'] or Decimal('0.0')
        loan_total = sum(loan.monthly_quota for loan in Loan.objects.filter(remaining_quotas__gt=0))
        egreso_planificado_total = budget_total + Decimal(str(loan_total))
        
        egreso_real_total = Transaction.objects.filter(
            date__year=year,
            date__month=month,
            is_income=False
        ).aggregate(t=Sum('amount'))['t'] or Decimal('0.0')
        
        delta = float(egreso_planificado_total) - float(egreso_real_total)
        
        return JsonResponse({
            'ingreso_total': float(ingreso_total),
            'egreso_planificado_total': float(egreso_planificado_total),
            'egreso_real_total': float(egreso_real_total),
            'delta': delta
        })

@login_required
def chart_api(request, year, month):
    categories = BudgetCategory.objects.all()
    results = []
    
    for cat in categories:
        plan = BudgetPlan.objects.filter(category=cat, year=year, month=month).first()
        planned_amount = plan.planned_amount if plan else Decimal('0.0')
        
        spent = Transaction.objects.filter(
            category=cat,
            date__year=year,
            date__month=month,
            is_income=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.0')
        
        results.append({
            'category_name': cat.name,
            'planned_amount': float(planned_amount),
            'real_spent': float(spent)
        })
        
    return JsonResponse({
        'year': year,
        'month': month,
        'categories': results
    })

@login_required
@require_POST
def register_loan_payment(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    if loan.register_payment():
        return JsonResponse({'status': 'success', 'message': 'Cuota descontada', 'remaining_quotas': loan.remaining_quotas})
    return JsonResponse({'status': 'error', 'message': 'El crédito ya está pagado.'}, status=400)

@login_required
@require_POST
def pay_all_loans(request):
    active_loans = Loan.objects.filter(remaining_quotas__gt=0)
    from .models import BudgetCategory, Transaction
    from django.utils import timezone
    cat, _ = BudgetCategory.objects.get_or_create(name="Créditos Bancarios", defaults={'is_essential': True})
    
    for loan in active_loans:
        loan.register_payment()
        Transaction.objects.create(
            date=timezone.now(),
            is_income=False,
            category=cat,
            amount=loan.monthly_quota,
            description=f"{loan.entity} - {loan.loan_type}"
        )
    return JsonResponse({'status': 'success', 'message': 'Todas las cuotas del mes descontadas y registradas como Egresos.'})

@login_required
@csrf_exempt
@require_POST
def simulate_prepayment_api(request):
    try:
        data = json.loads(request.body)
        extra_amount = Decimal(str(data.get('amount', 0)))
        result = LoanSimulator.simulate_prepayment(extra_amount)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
def duplicate_budget_api(request, pk):
    try:
        old_budget = get_object_or_404(Budget, pk=pk)
        data = json.loads(request.body)
        title = data.get('title')
        month = int(data.get('month'))
        year = int(data.get('year'))
        
        if Budget.objects.filter(month=month, year=year).exists():
            return JsonResponse({'status': 'error', 'message': 'Ya existe un presupuesto para ese mes y año.'}, status=400)
        
        new_budget = Budget.objects.create(title=title, month=month, year=year, total_budget=old_budget.total_budget)
        
        for detail in old_budget.details.all():
            detail.pk = None
            detail.budget = new_budget
            detail.save()
            
        return JsonResponse({'status': 'success', 'message': 'Presupuesto duplicado exitosamente.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        now = timezone.now()
        year, month = now.year, now.month
        
        # Ingresos Planificados y Reales
        ingresos_planificados = BudgetDetail.objects.filter(
            budget__year=year, budget__month=month, plan_type='ingreso'
        ).aggregate(t=Sum('total_amount'))['t'] or Decimal('0.0')
        ingresos_reales = Transaction.objects.filter(
            date__year=year, date__month=month, is_income=True
        ).aggregate(t=Sum('amount'))['t'] or Decimal('0.0')
        
        # Próximos Vencimientos (Loans)
        active_loans = Loan.objects.filter(remaining_quotas__gt=0)
        total_loan_quota = sum(loan.monthly_quota for loan in active_loans)
        
        # Gastos Reales
        gastos_reales = Transaction.objects.filter(
            date__year=year, date__month=month, is_income=False
        ).aggregate(t=Sum('amount'))['t'] or Decimal('0.0')
        
        # Gastos Planificados
        gastos_planificados = BudgetDetail.objects.filter(
            budget__year=year, budget__month=month, plan_type='egreso'
        ).aggregate(t=Sum('total_amount'))['t'] or Decimal('0.0')
        
        presupuesto_total = gastos_planificados
        gastos_totales_reales = gastos_reales
        
        # Remanente de ahorro real vs planificado
        remanente_real = ingresos_reales - gastos_totales_reales
        remanente_planificado = ingresos_planificados - presupuesto_total
        
        # Estado de cada categoría
        categories = BudgetCategory.objects.all()
        cat_status = []
        for cat in categories:
            plan_details = BudgetDetail.objects.filter(category=cat, budget__year=year, budget__month=month, plan_type='egreso')
            planned_amount = plan_details.aggregate(t=Sum('total_amount'))['t'] or Decimal('0.0')
            spent = Transaction.objects.filter(
                category=cat, date__year=year, date__month=month, is_income=False
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.0')
            
            percentage = (spent / planned_amount * 100) if planned_amount > 0 else (100 if spent > 0 else 0)
            
            if percentage < 80:
                color = 'bg-green-500'
                status = 'Verde'
            elif percentage <= 100:
                color = 'bg-yellow-500'
                status = 'Amarillo'
            else:
                color = 'bg-red-500'
                status = 'Rojo'
                
            cat_status.append({
                'name': cat.name,
                'planned': planned_amount,
                'spent': spent,
                'percentage': round(percentage, 1),
                'color': color,
                'status': status
            })
            
        progreso_presupuesto = (gastos_totales_reales / presupuesto_total * 100) if presupuesto_total > 0 else 0
        
        context = {
            'ingresos_planificados': ingresos_planificados,
            'ingresos_reales': ingresos_reales,
            'gastos_planificados': presupuesto_total,
            'gastos_reales': gastos_totales_reales,
            'remanente_real': remanente_real,
            'remanente_planificado': remanente_planificado,
            'progreso_presupuesto': min(100, round(progreso_presupuesto, 1)),
            'cat_status': cat_status,
            'active_loans': active_loans,
            'year': year,
            'month': month
        }
        return render(request, 'core/dashboard.html', context)

class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('transaction_list')
    extra_context = {'title': 'Registrar Gasto o Ingreso Variable'}

class LoanCreateView(LoginRequiredMixin, CreateView):
    model = Loan
    form_class = LoanForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('loan_list')
    extra_context = {'title': 'Añadir Nuevo Crédito'}

class IncomeSourceCreateView(LoginRequiredMixin, CreateView):
    model = IncomeSource
    form_class = IncomeSourceForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('income_list')
    extra_context = {'title': 'Configurar Fuente de Ingreso'}

class BudgetCreateView(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('budget_list')
    extra_context = {'title': 'Crear Presupuesto Maestro'}

class BudgetDetailCreateView(LoginRequiredMixin, CreateView):
    model = BudgetDetail
    form_class = BudgetDetailForm
    template_name = 'core/budgetplan_form.html'
    success_url = reverse_lazy('budgetdetail_list')
    extra_context = {'title': 'Añadir Detalle de Presupuesto'}

class BudgetCategoryCreateView(LoginRequiredMixin, CreateView):
    model = BudgetCategory
    form_class = BudgetCategoryForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('category_list')
    extra_context = {'title': 'Nueva Categoría'}

# --- LIST VIEWS ---
class TransactionMonthsListView(LoginRequiredMixin, ListView):
    template_name = 'core/transaction_months.html'
    context_object_name = 'months_data'
    
    def get_queryset(self):
        months = Transaction.objects.dates('date', 'month', order='DESC')
        data = []
        from django.db.models import Sum
        for m in months:
            qs = Transaction.objects.filter(date__year=m.year, date__month=m.month)
            ing = qs.filter(is_income=True).aggregate(t=Sum('amount'))['t'] or 0
            egr = qs.filter(is_income=False).aggregate(t=Sum('amount'))['t'] or 0
            data.append({
                'year': m.year,
                'month': m.month,
                'date': m,
                'ingresos': ing,
                'egresos': egr,
            })
        return data

class TransactionFilteredListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'core/generic_list.html'
    context_object_name = 'objects'
    
    def get_queryset(self):
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        return Transaction.objects.filter(date__year=year, date__month=month).order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils.formats import date_format
        import datetime
        dt = datetime.date(self.kwargs.get('year'), self.kwargs.get('month'), 1)
        context['title'] = f"Movimientos: {date_format(dt, 'F Y').capitalize()}"
        context['create_url'] = 'transaction_create'
        context['update_url_name'] = 'transaction_edit'
        context['delete_url_name'] = 'transaction_delete'
        return context

class LoanListView(LoginRequiredMixin, ListView):
    model = Loan
    template_name = 'core/generic_list.html'
    context_object_name = 'objects'
    extra_context = {'title': 'Créditos Bancarios', 'create_url': 'loan_create', 'update_url_name': 'loan_edit', 'delete_url_name': 'loan_delete'}

class IncomeSourceListView(LoginRequiredMixin, ListView):
    model = IncomeSource
    template_name = 'core/generic_list.html'
    context_object_name = 'objects'
    extra_context = {'title': 'Fuentes de Ingreso', 'create_url': 'income_create', 'update_url_name': 'income_edit', 'delete_url_name': 'income_delete'}

class BudgetListView(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'core/budget_list.html'
    context_object_name = 'objects'
    extra_context = {
        'title': 'Presupuestos Maestros',
        'create_url': 'budget_create',
        'update_url_name': 'budget_edit',
        'delete_url_name': 'budget_delete',
        'extra_action_url_name': 'budget_detail_filter',
        'extra_action_label': 'Ver Detalles'
    }

class BudgetDetailListView(LoginRequiredMixin, ListView):
    model = BudgetDetail
    template_name = 'core/generic_list.html'
    context_object_name = 'objects'
    extra_context = {'title': 'Detalles de Presupuesto', 'create_url': 'budgetdetail_create', 'update_url_name': 'budgetdetail_edit', 'delete_url_name': 'budgetdetail_delete'}

class BudgetManageDetailsView(LoginRequiredMixin, UpdateView):
    model = Budget
    fields = []
    template_name = 'core/budget_manage_details.html'
    success_url = reverse_lazy('budget_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .forms import BudgetDetailFormSet
        from .models import Loan
        from django.db.models import Sum
        
        if self.request.POST:
            context['formset'] = BudgetDetailFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = BudgetDetailFormSet(instance=self.object)
        context['title'] = f'Gestionar Detalles: {self.object.title}'
        
        loans_sum = Loan.objects.filter(remaining_quotas__gt=0).aggregate(Sum('monthly_quota'))['monthly_quota__sum'] or 0
        context['total_loans_quota'] = loans_sum
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class BudgetCategoryListView(LoginRequiredMixin, ListView):
    model = BudgetCategory
    template_name = 'core/generic_list.html'
    context_object_name = 'objects'
    extra_context = {'title': 'Categorías de Gastos', 'create_url': 'category_create', 'update_url_name': 'category_edit', 'delete_url_name': 'category_delete'}

# --- UPDATE VIEWS ---
class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('transaction_list')
    extra_context = {'title': 'Editar Movimiento'}

class LoanUpdateView(LoginRequiredMixin, UpdateView):
    model = Loan
    form_class = LoanForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('loan_list')
    extra_context = {'title': 'Editar Crédito'}

class IncomeSourceUpdateView(LoginRequiredMixin, UpdateView):
    model = IncomeSource
    form_class = IncomeSourceForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('income_list')
    extra_context = {'title': 'Editar Fuente de Ingreso'}

class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('budget_list')
    extra_context = {'title': 'Editar Presupuesto'}

class BudgetDetailUpdateView(LoginRequiredMixin, UpdateView):
    model = BudgetDetail
    form_class = BudgetDetailForm
    template_name = 'core/budgetplan_form.html'
    success_url = reverse_lazy('budgetdetail_list')
    extra_context = {'title': 'Editar Detalle'}

class BudgetCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = BudgetCategory
    form_class = BudgetCategoryForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('category_list')
    extra_context = {'title': 'Editar Categoría'}

# --- DELETE VIEWS ---
class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('transaction_list')

class LoanDeleteView(LoginRequiredMixin, DeleteView):
    model = Loan
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('loan_list')

class IncomeSourceDeleteView(LoginRequiredMixin, DeleteView):
    model = IncomeSource
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('income_list')

class BudgetDeleteView(LoginRequiredMixin, DeleteView):
    model = Budget
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('budget_list')

class BudgetDetailDeleteView(LoginRequiredMixin, DeleteView):
    model = BudgetDetail
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('budgetdetail_list')

class BudgetCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = BudgetCategory
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('category_list')

# --- ENTITY & LOANTYPE CRUD ---
class EntityListView(LoginRequiredMixin, ListView):
    model = Entity
    template_name = 'core/generic_list.html'
    context_object_name = 'objects'
    extra_context = {'title': 'Entidades Bancarias', 'create_url': 'entity_create', 'update_url_name': 'entity_edit', 'delete_url_name': 'entity_delete'}

class EntityCreateView(LoginRequiredMixin, CreateView):
    model = Entity
    form_class = EntityForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('entity_list')
    extra_context = {'title': 'Crear Entidad de Banco'}

class EntityUpdateView(LoginRequiredMixin, UpdateView):
    model = Entity
    form_class = EntityForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('entity_list')
    extra_context = {'title': 'Editar Entidad'}

class EntityDeleteView(LoginRequiredMixin, DeleteView):
    model = Entity
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('entity_list')

class LoanTypeListView(LoginRequiredMixin, ListView):
    model = LoanType
    template_name = 'core/generic_list.html'
    context_object_name = 'objects'
    extra_context = {'title': 'Tipos de Crédito', 'create_url': 'loantype_create', 'update_url_name': 'loantype_edit', 'delete_url_name': 'loantype_delete'}

class LoanTypeCreateView(LoginRequiredMixin, CreateView):
    model = LoanType
    form_class = LoanTypeForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('loantype_list')
    extra_context = {'title': 'Crear Tipo de Crédito'}

class LoanTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = LoanType
    form_class = LoanTypeForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('loantype_list')
    extra_context = {'title': 'Editar Tipo de Crédito'}

class LoanTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = LoanType
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('loantype_list')
