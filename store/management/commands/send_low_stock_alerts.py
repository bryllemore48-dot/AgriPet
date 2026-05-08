from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from store.models import Product


class Command(BaseCommand):
    help = 'Send low stock email alerts for active products that are below threshold.'

    def handle(self, *args, **options):
        low_stock_items = Product.objects.filter(stock__lt=5, is_active=True).order_by('stock')
        if not low_stock_items.exists():
            self.stdout.write(self.style.SUCCESS('No low-stock products found.'))
            return

        subject = 'Low Stock Alert: AgriPet Store'
        body_lines = ['The following products need restocking:']
        for product in low_stock_items:
            body_lines.append(f'- {product.name} ({product.store.name}): {product.stock} left')

        message = '\n'.join(body_lines)
        recipient_list = [settings.DEFAULT_FROM_EMAIL]
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            self.stdout.write(self.style.WARNING('Using console email backend. Email output will be printed to the console.'))

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=False)
        self.stdout.write(self.style.SUCCESS(f'Low stock alert sent to {recipient_list}.'))
