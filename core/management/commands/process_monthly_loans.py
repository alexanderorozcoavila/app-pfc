from django.core.management.base import BaseCommand
from core.models import Loan
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Descuenta automáticamente 1 cuota de todos los créditos activos. Diseñado para ejecutarse el día 1 de cada mes vía cron.'

    def handle(self, *args, **options):
        active_loans = Loan.objects.filter(remaining_quotas__gt=0)
        count = 0
        for loan in active_loans:
            if loan.register_payment():
                count += 1
                
        self.stdout.write(self.style.SUCCESS(f'[{count}] créditos han sido amortizados correctamente para este mes.'))
        logger.info(f"Monthly Loan Process: {count} quotas deducted.")
