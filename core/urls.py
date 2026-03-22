from django.urls import path
from . import views

urlpatterns = [
    path('api/comparison/<int:year>/<int:month>/', views.MonthlyComparisonView.as_view(), name='monthly_comparison'),
    path('api/charts/<int:year>/<int:month>/', views.chart_api, name='chart_api'),
    path('api/loans/<int:loan_id>/pay/', views.register_loan_payment, name='register_loan_payment'),
    path('api/loans/pay-all/', views.pay_all_loans, name='pay_all_loans'),
    path('api/simulate-prepayment/', views.simulate_prepayment_api, name='simulate_prepayment_api'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    path('transactions/', views.TransactionMonthsListView.as_view(), name='transaction_list'),
    path('transactions/<int:year>/<int:month>/', views.TransactionFilteredListView.as_view(), name='transaction_filtered'),
    path('transaction/new/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('transaction/<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_edit'),
    path('transaction/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),
    
    path('loans/', views.LoanListView.as_view(), name='loan_list'),
    path('loan/new/', views.LoanCreateView.as_view(), name='loan_create'),
    path('loan/<int:pk>/edit/', views.LoanUpdateView.as_view(), name='loan_edit'),
    path('loan/<int:pk>/delete/', views.LoanDeleteView.as_view(), name='loan_delete'),
    
    path('incomes/', views.IncomeSourceListView.as_view(), name='income_list'),
    path('income/new/', views.IncomeSourceCreateView.as_view(), name='income_create'),
    path('income/<int:pk>/edit/', views.IncomeSourceUpdateView.as_view(), name='income_edit'),
    path('income/<int:pk>/delete/', views.IncomeSourceDeleteView.as_view(), name='income_delete'),
    
    path('budgets/', views.BudgetListView.as_view(), name='budget_list'),
    path('budget/new/', views.BudgetCreateView.as_view(), name='budget_create'),
    path('budget/<int:pk>/edit/', views.BudgetUpdateView.as_view(), name='budget_edit'),
    path('budget/<int:pk>/delete/', views.BudgetDeleteView.as_view(), name='budget_delete'),
    path('budget/<int:pk>/duplicate/', views.duplicate_budget_api, name='budget_duplicate'),
    
    path('budget-details/', views.BudgetDetailListView.as_view(), name='budgetdetail_list'),
    path('budget/<int:pk>/details/', views.BudgetManageDetailsView.as_view(), name='budget_detail_filter'),
    path('budget-detail/new/', views.BudgetDetailCreateView.as_view(), name='budgetdetail_create'),
    path('budget-detail/<int:pk>/edit/', views.BudgetDetailUpdateView.as_view(), name='budgetdetail_edit'),
    path('budget-detail/<int:pk>/delete/', views.BudgetDetailDeleteView.as_view(), name='budgetdetail_delete'),
    
    path('categories/', views.BudgetCategoryListView.as_view(), name='category_list'),
    path('category/new/', views.BudgetCategoryCreateView.as_view(), name='category_create'),
    path('category/<int:pk>/edit/', views.BudgetCategoryUpdateView.as_view(), name='category_edit'),
    path('category/<int:pk>/delete/', views.BudgetCategoryDeleteView.as_view(), name='category_delete'),
    
    path('entities/', views.EntityListView.as_view(), name='entity_list'),
    path('entity/new/', views.EntityCreateView.as_view(), name='entity_create'),
    path('entity/<int:pk>/edit/', views.EntityUpdateView.as_view(), name='entity_edit'),
    path('entity/<int:pk>/delete/', views.EntityDeleteView.as_view(), name='entity_delete'),
    
    path('loantypes/', views.LoanTypeListView.as_view(), name='loantype_list'),
    path('loantype/new/', views.LoanTypeCreateView.as_view(), name='loantype_create'),
    path('loantype/<int:pk>/edit/', views.LoanTypeUpdateView.as_view(), name='loantype_edit'),
    path('loantype/<int:pk>/delete/', views.LoanTypeDeleteView.as_view(), name='loantype_delete'),
]
