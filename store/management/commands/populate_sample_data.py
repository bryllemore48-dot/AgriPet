import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from store.models import Store, Product, Customer, Staff, Order, OrderItem


class Command(BaseCommand):
    help = 'Populate the database with sample stores, products, customers, staff, and orders.'

    def handle(self, *args, **options):
        if Store.objects.exists():
            self.stdout.write(self.style.WARNING('Data already exists. Aborting sample data population.'))
            return

        livestock = Store.objects.create(
            name='Livestock Store',
            store_type=Store.LIVESTOCK,
            description='Livestock supplies and animal feed',
        )
        agripet = Store.objects.create(
            name='AgriPet Store',
            store_type=Store.AGRIPET,
            description='Pet care and pet nutrition products',
        )

        products = [
            {'name': 'Broiler Chicken', 'category': 'chicken', 'store': livestock, 'price_per_kilo': 280.00, 'stock_in_sacks': 32},
            {'name': 'Starter Piglet', 'category': 'pig', 'store': livestock, 'price_per_kilo': 620.00, 'stock_in_sacks': 18},
            {'name': 'Pet Dog Food', 'category': 'feeds', 'store': agripet, 'price_per_kilo': 450.00, 'stock_in_sacks': 24},
            {'name': 'Cat Dry Food', 'category': 'feeds', 'store': agripet, 'price_per_kilo': 220.00, 'stock_in_sacks': 29},
            {'name': 'K9 Working Dog', 'category': 'dog', 'store': agripet, 'price_per_kilo': 1200.00, 'stock_in_sacks': 8},
            {'name': 'House Cat', 'category': 'cat', 'store': agripet, 'price_per_kilo': 800.00, 'stock_in_sacks': 10},
        ]

        for product_data in products:
            Product.objects.create(**product_data)

        customers = [
            {'name': 'Miriam Dela Cruz', 'email': 'miriam@example.com', 'phone': '09171234567', 'address': 'Makati City'},
            {'name': 'Jose Santos', 'email': 'jose@example.com', 'phone': '09179876543', 'address': 'Cebu City'},
        ]
        customer_objects = [Customer.objects.create(**data) for data in customers]

        staff_members = [
            {'name': 'Ramon Garcia', 'email': 'ramon@example.com', 'phone': '09171112222', 'store': livestock, 'role': 'Farm Supervisor'},
            {'name': 'Anna Reyes', 'email': 'anna@example.com', 'phone': '09172223333', 'store': agripet, 'role': 'Store Manager'},
        ]
        staff_objects = [Staff.objects.create(**data) for data in staff_members]

        product_list = list(Product.objects.all())
        for i in range(2):
            order = Order.objects.create(
                customer=random.choice(customer_objects),
                store=random.choice([livestock, agripet]),
                status=Order.STATUS_COMPLETED,
                total_amount=0,
            )
            order_items = []
            for _ in range(2):
                product = random.choice(product_list)
                quantity = random.randint(1, 4)
                if product.stock < quantity:
                    quantity = product.stock
                if quantity == 0:
                    continue
                product.stock = max(product.stock - quantity, 0)
                product.save()
                item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=product.price,
                )
                order_items.append(item)
            order.total_amount = sum(item.subtotal for item in order_items)
            order.save()

        self.stdout.write(self.style.SUCCESS('Sample data created successfully.'))
