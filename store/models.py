from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.validators import MinValueValidator


class Store(models.Model):
    LIVESTOCK = 'livestock'
    AGRIPET = 'agripet'
    STORE_TYPE_CHOICES = [
        (LIVESTOCK, 'Cebuana Padala'),
        (AGRIPET, 'AgriPet Store'),
    ]

    name = models.CharField(max_length=120, editable=False)
    store_type = models.CharField(max_length=16, choices=STORE_TYPE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Store'
        verbose_name_plural = 'Stores'
        ordering = ['name']

    def get_store_label(self):
        return dict(self.STORE_TYPE_CHOICES).get(self.store_type, 'Store')

    def save(self, *args, **kwargs):
        self.name = self.get_store_label()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('chicken', 'Chicken'),
        ('pig', 'Pig'),
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('feeds', 'Feeds'),
    ]

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=140)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES)
    price_per_kilo = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock_in_sacks = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def stock_status(self):
        if self.stock_in_sacks == 0:
            return 'out_of_stock'
        if self.stock_in_sacks < 5:
            return 'low_stock'
        return 'in_stock'

    @property
    def stock_label(self):
        return {
            'out_of_stock': 'Out of stock',
            'low_stock': 'Low stock',
            'in_stock': 'In stock',
        }[self.stock_status]


class ServiceTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('send', 'Send Money'),
        ('receive', 'Receive Money'),
        ('bills', 'Bills Payment'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='service_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Service Transaction'
        verbose_name_plural = 'Service Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.transaction_type} - {self.reference_number}'


class Customer(models.Model):
    name = models.CharField(max_length=140)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['name']

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    order_number = models.CharField(max_length=40, unique=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name='Supplier', help_text='Supplier of feeds for this order')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = timezone.now().strftime('ORD%Y%m%d%H%M%S%f')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number

    @property
    def item_count(self):
        return self.items.count()

    @property
    def computed_total(self):
        return sum(item.subtotal for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f'{self.product.name} × {self.quantity}'

    @property
    def subtotal(self):
        if self.unit_price is None:
            return 0
        return self.quantity * self.unit_price


class PaymentProof(models.Model):
    PAYMENT_RECEIPT = 'receipt'
    DELIVERY_PROOF = 'delivery'
    OTHER = 'other'
    PROOF_TYPE_CHOICES = [
        (PAYMENT_RECEIPT, 'Payment Receipt'),
        (DELIVERY_PROOF, 'Delivery Proof'),
        (OTHER, 'Other Document'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment_proof')
    proof_type = models.CharField(max_length=16, choices=PROOF_TYPE_CHOICES, default=PAYMENT_RECEIPT)
    image = models.ImageField(upload_to='payment_proofs/')
    verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Payment Proof'
        verbose_name_plural = 'Payment Proofs'

    def __str__(self):
        return f'Proof for {self.order.order_number}'


class Staff(models.Model):
    name = models.CharField(max_length=140)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='staff')
    role = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    hired_at = models.DateField(default=timezone.now)

    class Meta:
        verbose_name = 'Staff'
        verbose_name_plural = 'Staff Members'
        ordering = ['name']

    def __str__(self):
        return self.name


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('half_day', 'Half Day'),
        ('absent', 'Absent'),
        ('on_leave', 'On Leave'),
    ]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        ordering = ['-date', 'staff__name']
        unique_together = ('staff', 'date')

    def __str__(self):
        return f'{self.staff.name} – {self.date}'

    @property
    def duration_hours(self):
        if self.time_in and self.time_out:
            delta = timezone.datetime.combine(timezone.now().date(), self.time_out) - timezone.datetime.combine(timezone.now().date(), self.time_in)
            return round(delta.total_seconds() / 3600, 2)
        return 0


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return self.user.get_full_name() or self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
