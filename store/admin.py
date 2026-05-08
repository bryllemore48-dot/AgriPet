from django.contrib import admin
from .models import Store, Product, Customer, Order, OrderItem, PaymentProof, Staff, Attendance, UserProfile


class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'store_type', 'description')
    readonly_fields = ('name',)
    list_filter = ('store_type',)


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
        # Only superusers can delete products
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        # Only staff can change products
        return request.user.is_staff
    
    def has_add_permission(self, request, obj=None):
        # Only staff can add products
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
            from django.utils.html import format_html
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 300px; border-radius: 8px; margin-top: 10px;" />',
                obj.image.url
            )
        return 'No image uploaded yet'
    image_preview.short_description = 'Image Preview'


class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'store', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'store', 'created_at')
    search_fields = ('order_number',)
    inlines = [OrderItemInline, PaymentProofInline]
    readonly_fields = ('order_number', 'created_at', 'updated_at')


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
admin.site.register(Staff)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
