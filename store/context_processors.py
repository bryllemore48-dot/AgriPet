from .models import Product, Order, UserProfile


def notification_context(request):
    low_stock_products = Product.objects.filter(stock_in_sacks__lt=5, is_active=True)
    low_stock_count = low_stock_products.count()
    recent_orders = Order.objects.order_by('-created_at')[:3]
    notifications = []
    for product in low_stock_products[:5]:
        notifications.append({
            'type': 'Low stock',
            'message': f'{product.name} has low stock ({product.stock_in_sacks} sacks left)',
            'link': '#',
        })
    for order in recent_orders:
        notifications.append({
            'type': 'Order',
            'message': f'Order {order.order_number} updated',
            'link': '#',
        })
    profile = None
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            profile = None
    return {
        'low_stock_count': low_stock_count,
        'recent_orders': recent_orders,
        'notifications': notifications,
        'user_profile': profile,
    }
