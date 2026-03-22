from django.contrib import admin
from .models import IncomeSource, Loan, Budget, BudgetDetail, Transaction, BudgetCategory, Entity, LoanType

admin.site.register(IncomeSource)
admin.site.register(Loan)
admin.site.register(Budget)
admin.site.register(BudgetDetail)
admin.site.register(Transaction)
admin.site.register(BudgetCategory)
admin.site.register(Entity)
admin.site.register(LoanType)
