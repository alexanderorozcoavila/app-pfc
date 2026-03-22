from core.forms import IncomeSourceForm, LoanForm
from core.models import Entity, LoanType
e = Entity.objects.create(name='Test Bank')
lt = LoanType.objects.create(name='Test Loan')
f = IncomeSourceForm({'entity': e.id, 'description': 'salario', 'amount': '2.600.000', 'is_fixed': True})
print('Income valid:', f.is_valid(), f.errors)
f2 = LoanForm({'entity': e.id, 'loan_type': lt.id, 'monthly_quota': '347.773', 'total_quotas': 12, 'remaining_quotas': 12, 'start_date': '2026-03-22'})
print('Loan valid:', f2.is_valid(), f2.errors)
