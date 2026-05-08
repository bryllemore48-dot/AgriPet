from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from .models import Store, Product, Order, Attendance, UserProfile, Customer, ServiceTransaction
from .forms import UserForm, UserProfileForm
@login_required
def dashboard(request):
    selected_range = request.GET.get('range', '7')
    if selected_range not in ['7', '30']:
        selected_range = '7'

    stores = Store.objects.all()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    low_stock_products = Product.objects.filter(stock_in_sacks__lt=5).count()
    active_stores = stores.count()
    recent_orders = Order.objects.order_by('-created_at')[:7]
    latest_products = Product.objects.order_by('-updated_at')[:8]

    today = datetime.now().date()
    days = int(selected_range)
    start_date = today - timedelta(days=days - 1)
    stores_range = [start_date + timedelta(days=i) for i in range(days)]

    completed_orders = Order.objects.filter(
        status=Order.STATUS_COMPLETED,
        created_at__date__gte=start_date,
        created_at__date__lte=today,
    )

    daily_stores = {day: 0.0 for day in stores_range}
    for order in completed_orders:
        order_date = order.created_at.date()
        if order_date in daily_stores:
            daily_stores[order_date] += float(order.total_amount or 0)

    stores_labels = [f'Day {i + 1}' for i in range(days)]
    stores_values = [daily_stores[day] for day in stores_range]

    total_stores = sum(stores_values)
    total_orders_range = completed_orders.count()
    average_order_value = total_stores / total_orders_range if total_orders_range else 0
    peak_stores = max(stores_values) if stores_values else 0

    # Calculate profit overview by store and period
    today = datetime.now().date()
    month_start = today.replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end = next_month - timedelta(days=1)
    
    # Calculate profit for each store (this month)
    store_profits_list = []
    max_profit = 0
    for store in stores:
        store_profit = Order.objects.filter(
            store=store,
            status=Order.STATUS_COMPLETED,
            created_at__date__gte=month_start,
            created_at__date__lte=today,
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        store_profits_list.append({
            'store': store,
            'profit': store_profit,
        })
        max_profit = max(max_profit, store_profit)

    context = {
        'stores': stores,
        'total_products': total_products,
        'total_orders': total_orders,
        'low_stock_products': low_stock_products,
        'active_stores': active_stores,
        'recent_orders': recent_orders,
        'latest_products': latest_products,
        'stores_labels': stores_labels,
        'stores_values': stores_values,
        'total_stores': total_stores,
        'average_order_value': average_order_value,
        'total_orders_range': total_orders_range,
        'peak_stores': peak_stores,
        'selected_range': selected_range,
        'store_profits_list': store_profits_list,
        'max_profit': max_profit,
    }
    return render(request, 'store/dashboard.html', context)


@login_required
def store_detail(request, store_type):
    store = get_object_or_404(Store, store_type=store_type)
    today = datetime.now().date()
    week_start = today - timedelta(days=6)

    if store.store_type == 'agripet':
        # Product-based inventory for AgriPet Store
        products = Product.objects.filter(store=store).order_by('-stock_in_sacks')
        total_products = products.count()
        in_stock = products.filter(stock_in_sacks__gte=5).count()
        low_stock = products.filter(stock_in_sacks__gt=0, stock_in_sacks__lt=5).count()
        out_of_stock = products.filter(stock_in_sacks=0).count()

        weekly_orders = Order.objects.filter(
            store=store,
            status=Order.STATUS_COMPLETED,
            created_at__date__gte=week_start,
            created_at__date__lte=today,
        ).order_by('-created_at')[:12]

        total_profit_week = weekly_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        average_order_value = total_profit_week / weekly_orders.count() if weekly_orders.count() else 0

        context = {
            'store': store,
            'is_product_store': True,
            'products': products,
            'total_products': total_products,
            'total_profit_week': total_profit_week,
            'average_order_value': average_order_value,
            'in_stock': in_stock,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'weekly_orders': weekly_orders,
            'week_start': week_start,
            'today': today,
        }
    else:
        # Service-based transactions for Cebuana Padala
        service_transactions = ServiceTransaction.objects.filter(store=store).order_by('-created_at')
        total_transactions = service_transactions.count()
        completed = service_transactions.filter(status='completed').count()
        pending = service_transactions.filter(status='pending').count()
        failed = service_transactions.filter(status='failed').count()

        weekly_transactions = service_transactions.filter(
            created_at__date__gte=week_start,
            created_at__date__lte=today,
        )[:12]

        total_amount_week = service_transactions.filter(
            created_at__date__gte=week_start,
            created_at__date__lte=today,
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        context = {
            'store': store,
            'is_product_store': False,
            'service_transactions': service_transactions,
            'total_transactions': total_transactions,
            'total_amount_week': total_amount_week,
            'completed': completed,
            'pending': pending,
            'failed': failed,
            'weekly_transactions': weekly_transactions,
            'week_start': week_start,
            'today': today,
        }

    return render(request, 'store/store_detail.html', context)


@login_required
def store_pdf(request, store_type):
    store = get_object_or_404(Store, store_type=store_type)
    today = datetime.now().date()
    week_start = today - timedelta(days=6)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{store.name}_report_{today}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=30)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, spaceAfter=20)
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])

    elements = []

    # Title
    elements.append(Paragraph(f"{store.name} - Weekly Report", title_style))
    elements.append(Paragraph(f"Report Date: {today.strftime('%B %d, %Y')}", subtitle_style))
    elements.append(Paragraph(f"Week: {week_start.strftime('%B %d')} - {today.strftime('%B %d, %Y')}", subtitle_style))
    elements.append(Spacer(1, 20))

    if store.store_type == 'agripet':
        # Product store
        products = Product.objects.filter(store=store).order_by('-stock_in_sacks')
        weekly_orders = Order.objects.filter(
            store=store,
            status=Order.STATUS_COMPLETED,
            created_at__date__gte=week_start,
            created_at__date__lte=today,
        ).order_by('-created_at')[:12]
        total_profit_week = weekly_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        elements.append(Paragraph(f"Total Weekly Profit: ₱{total_profit_week:.2f}", styles['Heading2']))
        elements.append(Spacer(1, 10))

        # Inventory Table
        data = [['Product', 'Category', 'Price', 'Stock', 'Status']]
        for product in products:
            data.append([
                product.name,
                product.get_category_display(),
                f"₱{product.price_per_kilo} / kg",
                f"{product.stock_in_sacks} sacks",
                product.stock_label
            ])
        table = Table(data)
        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 20))

        # Weekly Orders Table
        elements.append(Paragraph("Weekly Transactions", styles['Heading3']))
        order_data = [['Order Number', 'Date', 'Status', 'Total']]
        for order in weekly_orders:
            order_data.append([
                order.order_number,
                order.created_at.strftime('%m/%d/%Y'),
                order.get_status_display(),
                f"₱{order.total_amount:.2f}"
            ])
        order_table = Table(order_data)
        order_table.setStyle(table_style)
        elements.append(order_table)

    else:
        # Service store
        service_transactions = ServiceTransaction.objects.filter(store=store).order_by('-created_at')
        weekly_transactions_full = service_transactions.filter(
            created_at__date__gte=week_start,
            created_at__date__lte=today,
        )
        weekly_transactions = weekly_transactions_full[:12]
        total_amount_week = weekly_transactions_full.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0

        elements.append(Paragraph(f"Total Weekly Amount: ₱{total_amount_week:.2f}", styles['Heading2']))
        elements.append(Spacer(1, 10))

        # Transactions Table
        data = [['Type', 'Reference', 'Customer', 'Amount', 'Status']]
        for transaction in service_transactions:
            data.append([
                transaction.get_transaction_type_display(),
                transaction.reference_number,
                transaction.customer_name,
                f"₱{transaction.amount:.2f}",
                transaction.get_status_display()
            ])
        table = Table(data)
        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 20))

        # Weekly Transactions Table
        elements.append(Paragraph("Weekly Transactions", styles['Heading3']))
        weekly_data = [['Type', 'Reference', 'Date', 'Amount']]
        for transaction in weekly_transactions:
            weekly_data.append([
                transaction.get_transaction_type_display(),
                transaction.reference_number,
                transaction.created_at.strftime('%m/%d/%Y'),
                f"₱{transaction.amount:.2f}"
            ])
        weekly_table = Table(weekly_data)
        weekly_table.setStyle(table_style)
        elements.append(weekly_table)

    doc.build(elements)
    return response


@login_required
def dashboard_dark(request):
    selected_range = request.GET.get('range', '7')
    if selected_range not in ['7', '30']:
        selected_range = '7'

    stores = Store.objects.all()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    low_stock_products = Product.objects.filter(stock_in_sacks__lt=5).count()
    recent_orders = Order.objects.order_by('-created_at')[:7]
    latest_products = Product.objects.order_by('-updated_at')[:8]

    today = datetime.now().date()
    days = int(selected_range)
    start_date = today - timedelta(days=days - 1)
    stores_range = [start_date + timedelta(days=i) for i in range(days)]

    completed_orders = Order.objects.filter(
        status=Order.STATUS_COMPLETED,
        created_at__date__gte=start_date,
        created_at__date__lte=today,
    )

    daily_stores = {day: 0.0 for day in stores_range}
    for order in completed_orders:
        order_date = order.created_at.date()
        if order_date in daily_stores:
            daily_stores[order_date] += float(order.total_amount or 0)

    stores_labels = [f'Day {i + 1}' for i in range(days)]
    stores_values = [daily_stores[day] for day in stores_range]

    total_stores = sum(stores_values)
    total_orders_range = completed_orders.count()
    average_order_value = total_stores / total_orders_range if total_orders_range else 0
    peak_stores = max(stores_values) if stores_values else 0

    context = {
        'stores': stores,
        'total_products': total_products,
        'total_orders': total_orders,
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
        'latest_products': latest_products,
        'stores_labels': stores_labels,
        'stores_values': stores_values,
        'total_stores': total_stores,
        'average_order_value': average_order_value,
        'total_orders_range': total_orders_range,
        'peak_stores': peak_stores,
        'selected_range': selected_range,
    }
    return render(request, 'store/dashboard_dark.html', context)


@login_required
def frontend_app(request):
    return render(request, 'store/frontend_app.html')



@login_required
def inventory_list(request):
    # All users see the same shared inventory (not filtered by user)
    # Only admins can modify inventory through this interface
    
    store_id = request.GET.get('store')
    selected_store = None
    current_store_type = None
    if store_id:
        try:
            selected_store = int(store_id)
            current_store = Store.objects.filter(id=selected_store).first()
            if current_store:
                current_store_type = current_store.store_type
        except ValueError:
            selected_store = None
    
    # Fetch all products (shared across all users - not filtered by user_id)
    products = Product.objects.select_related('store').all()
    if selected_store:
        products = products.filter(store_id=selected_store)

    stores = Store.objects.all()
    context = {
        'products': products,
        'stores': stores,
        'selected_store': selected_store,
        'current_store_type': current_store_type,
        'is_admin': request.user.is_staff,  # Show admin controls only for admins
    }
    return render(request, 'store/inventory_list.html', context)


@login_required
def shop_list(request):
    # All users see the same shared inventory (not filtered by user)
    # This is a public/customer view of available products
    
    products = Product.objects.filter(is_active=True, stock_in_sacks__gt=0).select_related('store')
    stores = Store.objects.all()

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(name__icontains=search_query)

    # Category filter
    category = request.GET.get('category', '')
    if category:
        products = products.filter(category=category)

    # Store filter
    store_id = request.GET.get('store', '')
    if store_id:
        products = products.filter(store_id=store_id)

    context = {
        'products': products,
        'stores': stores,
        'search_query': search_query,
        'selected_category': category,
        'selected_store': store_id,
        'categories': Product.CATEGORY_CHOICES,
    }
    return render(request, 'store/shop_list.html', context)

@login_required
def report_with_proof(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    orders = Order.objects.select_related('store').prefetch_related('payment_proof').order_by('-created_at')
    if start_date:
        orders = orders.filter(created_at__date__gte=start_date)
    if end_date:
        orders = orders.filter(created_at__date__lte=end_date)

    context = {
        'orders': orders,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'store/report_with_proof.html', context)


@login_required
def user_settings(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please sign in to manage your settings.')
        return redirect('store:dashboard')

    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user_form = UserForm(request.POST or None, instance=request.user)
    profile_form = UserProfileForm(request.POST or None, request.FILES or None, instance=user_profile)
    password_form = PasswordChangeForm(user=request.user, data=request.POST or None)

    if request.method == 'POST':
        if 'save_profile' in request.POST and user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('store:user_settings')
        if 'change_password' in request.POST and password_form.is_valid():
            password_form.save()
            update_session_auth_hash(request, password_form.user)
            messages.success(request, 'Password changed successfully.')
            return redirect('store:user_settings')

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
        'user_profile': user_profile,
    }
    return render(request, 'store/user_settings.html', context)


@login_required
def attendance_list(request):
    attendances = Attendance.objects.select_related('staff', 'staff__store').order_by('-date')[:30]
    context = {
        'attendances': attendances,
    }
    return render(request, 'store/attendance_list.html', context)


@login_required
def profit(request):
    store_param = request.GET.get('store')
    period = request.GET.get('period', 'today')

    # Map store param to a concrete store name identifier
    store_name_map = {
        'agripet': 'AgriPet Store',
        'cebuanapadala': 'Cebuana Padala'
    }
    store_name = store_name_map.get(store_param)

    if not store_name:
        messages.error(request, 'Invalid store selected.')
        return redirect('store:dashboard')

    # Get the store by its unique display label
    try:
        store = Store.objects.get(name=store_name)
    except Store.DoesNotExist:
        messages.error(request, 'Store not found.')
        return redirect('store:dashboard')
    except Store.MultipleObjectsReturned:
        store = Store.objects.filter(name=store_name).first()
        if not store:
            messages.error(request, 'Store not found.')
            return redirect('store:dashboard')

    # Calculate date range
    from datetime import datetime, timedelta
    today = datetime.now().date()

    if period == 'today':
        start_date = today
        end_date = today
        period_label = 'Today'
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        period_label = 'This Week'
    elif period == 'month':
        start_date = today.replace(day=1)
        next_month = start_date.replace(month=start_date.month % 12 + 1, day=1)
        end_date = next_month - timedelta(days=1)
        period_label = 'This Month'
    else:
        messages.error(request, 'Invalid period selected.')
        return redirect('store:dashboard')

    # Filter orders
    orders = Order.objects.filter(
        store=store,
        status=Order.STATUS_COMPLETED,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    # Calculate profit (total stores)
    total_profit = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    order_count = orders.count()

    context = {
        'store': store,
        'period_label': period_label,
        'total_profit': total_profit,
        'order_count': order_count,
        'orders': orders[:10],  # Show last 10 orders
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'store/profit.html', context)


def register(request):
    if request.user.is_authenticated:
        return redirect('store:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not username or not email or not password1 or not password2:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('store:register')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('store:register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('store:register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('store:register')

        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        messages.success(request, 'Registration successful!')
        return redirect('store:dashboard')

    return render(request, 'store/register.html')


def user_login(request):
    if request.user.is_authenticated:
        return redirect('store:dashboard')

    next_url = request.GET.get('next') or request.POST.get('next', '')
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'Login successful!')
            if next_url:
                return redirect(next_url)
            return redirect('store:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'store/login.html', {'form': form, 'next': next_url})


def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('store:login')


def frontend_login(request):
    if request.user.is_authenticated:
        return redirect('store:dashboard')

    next_url = request.GET.get('next') or request.POST.get('next', '')
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'Login successful!')
            if next_url:
                return redirect(next_url)
            return redirect('store:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'frontend/login.html', {'form': form, 'next': next_url})
