from decimal import Decimal
from .models import Loan

class LoanSimulator:
    @staticmethod
    def simulate_prepayment(extra_amount: Decimal):
        """
        Simula la aplicación de un monto extra a los créditos activos.
        Prioriza por menor saldo (ya que el modelo no contiene campo de tasa de interés).
        Retorna un reporte comparativo del impacto.
        """
        # 1. Obtener créditos activos
        active_loans = Loan.objects.filter(remaining_quotas__gt=0)
        
        # 2. Calcular saldo estimado de cada uno: cuota_mensual * cuotas_restantes
        loans_with_balance = []
        for loan in active_loans:
            balance = loan.monthly_quota * loan.remaining_quotas
            loans_with_balance.append({
                'loan': loan,
                'balance': balance
            })
            
        # 3. Ordenar por menor saldo
        loans_with_balance.sort(key=lambda x: x['balance'])
        
        remaining_extra = Decimal(str(extra_amount))
        report = []
        
        for item in loans_with_balance:
            if remaining_extra <= 0:
                break
                
            loan = item['loan']
            quota = loan.monthly_quota
            
            # Si el monto extra permite pagar al menos una cuota completa
            if remaining_extra >= quota and quota > 0:
                quotas_to_pay = int(remaining_extra // quota)
                
                # No pagar más de las cuotas restantes
                if quotas_to_pay > loan.remaining_quotas:
                    quotas_to_pay = loan.remaining_quotas
                
                amount_used = Decimal(str(quotas_to_pay)) * quota
                remaining_extra -= amount_used
                
                report.append({
                    'entity': loan.entity.name if loan.entity else 'N/A',
                    'loan_type': loan.loan_type.name if loan.loan_type else 'N/A',
                    'months_saved': int(quotas_to_pay),
                    'released_monthly': float(quota),
                    'message': f"Si pagas el Crédito {loan.entity.name if loan.entity else 'N/A'} hoy, liberarás ${quota:,.0f} mensuales {quotas_to_pay} meses antes."
                })

        return {
            'monto_inicial': float(extra_amount),
            'monto_restante': float(remaining_extra),
            'reporte': report
        }
