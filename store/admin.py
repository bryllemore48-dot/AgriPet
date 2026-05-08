from django.contrib import admin
from django.urls import reverse, path
from django.utils.html import format_html
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from .models import (
    Store, Product, Customer, Order, OrderItem,
    PaymentProof, Staff, Attendance, UserProfile,
    ServiceTransaction,
)


# ---------------------------------------------------------------------------
# Context builder — mirrors your store:store_detail view
# ---------------------------------------------------------------------------

def _build_store_context(store):
    today = timezone.now().date()
    week_start = today - timezone.timedelta(days=today.weekday())  # Monday
    is_product_store = store.store_type == Store.AGRIPET

    context = {
        'store': store,
        'is_product_store': is_product_store,
        'today': today,
        'week_start': week_start,
    }

    if is_product_store:
        products = Product.objects.filter(store=store)

        weekly_orders = (
            Order.objects.filter(
                store=store,
                status=Order.STATUS_COMPLETED,
                created_at__date__gte=week_start,
            )
            .order_by('-created_at')[:12]
        )
        total_profit_week = sum(o.total_amount for o in weekly_orders)

        context.update({
            'products': products,
            'total_products': products.count(),
            'in_stock':     sum(1 for p in products if p.stock_status == 'in_stock'),
            'low_stock':    sum(1 for p in products if p.stock_status == 'low_stock'),
            'out_of_stock': sum(1 for p in products if p.stock_status == 'out_of_stock'),
            'weekly_orders': weekly_orders,
            'total_profit_week': total_profit_week,
        })

    else:
        all_tx = ServiceTransaction.objects.filter(store=store)
        weekly_tx = (
            all_tx
            .filter(created_at__date__gte=week_start)
            .order_by('-created_at')[:12]
        )
        total_amount_week = sum(t.amount for t in weekly_tx)

        context.update({
            'service_transactions': all_tx,
            'total_transactions':   all_tx.count(),
            'completed': all_tx.filter(status='completed').count(),
            'pending':   all_tx.filter(status='pending').count(),
            'failed':    all_tx.filter(status='failed').count(),
            'weekly_transactions': weekly_tx,
            'total_amount_week':   total_amount_week,
        })

    return context


# ---------------------------------------------------------------------------
# Admin classes
# ---------------------------------------------------------------------------

class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'store_type', 'description', 'store_detail_link')
    readonly_fields = ('name',)
    list_filter = ('store_type',)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<int:store_id>/detail/',
                self.admin_site.admin_view(self.store_detail_view),
                name='store_store_detail',
            ),
        ]
        return custom + urls

    def store_detail_view(self, request, store_id):
        store = get_object_or_404(Store, pk=store_id)
        ctx = _build_store_context(store)
        ctx.update(self.admin_site.each_context(request))
        ctx['title'] = f'{store.name} — Detail'
        ctx['opts'] = self.model._meta
        return TemplateResponse(
            request,
            'admin/store/store/store_detail.html',
            ctx,
        )

    def store_detail_link(self, obj):
        url = reverse('admin:store_store_detail', args=[obj.pk])
        return format_html('<a href="{}">View detail →</a>', url)
    store_detail_link.short_description = 'Detail'


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'category', 'price_per_kilo', 'stock_in_sacks', 'stock_status')
    list_filter = ('store', 'category', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('stock_status', 'created_at', 'updated_at')
    fieldsets = (
        ('Product Information', {
            'fields': ('store', 'name', 'category', 'description', 'is_active')
        }),
        ('Inventory & Pricing', {
            'fields': ('price_per_kilo', 'stock_in_sacks', 'stock_status')
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_add_permission(self, request, obj=None):
        return request.user.is_staff


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal',)


class PaymentProofInline(admin.StackedInline):
    model = PaymentProof
    extra = 1
    readonly_fields = ('created_at', 'image_preview')
    fields = ('proof_type', 'image', 'image_preview', 'verified', 'notes', 'created_at')

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:400px;max-height:300px;'
                'border-radius:8px;margin-top:10px;" />',
                obj.image.url,
            )
        return 'No image uploaded yet'
    image_preview.short_description = 'Image Preview'


class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'store_link', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'store', 'created_at')
    search_fields = ('order_number',)
    inlines = [OrderItemInline, PaymentProofInline]
    readonly_fields = ('order_number', 'created_at', 'updated_at')

    def store_link(self, obj):
        url = reverse('store:store_detail', args=[obj.store.store_type])
        return format_html('<a href="{}">{}</a>', url, obj.store.name)
    store_link.short_description = 'Store'


class ServiceTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'store', 'transaction_type', 'customer_name', 'amount', 'status', 'created_at')
    list_filter = ('store', 'transaction_type', 'status', 'created_at')
    search_fields = ('reference_number', 'customer_name')
    readonly_fields = ('created_at',)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
    readonly_fields = ('updated_at',)


class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('staff', 'date', 'status', 'time_in', 'time_out')
    list_filter = ('status', 'date', 'staff__store')
    search_fields = ('staff__name',)


admin.site.register(Store, StoreAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Customer)
admin.site.register(Order, OrderAdmin)
admin.site.register(ServiceTransaction, ServiceTransactionAdmin)
admin.site.register(Staff)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(UserProfile, UserProfileAdmin)