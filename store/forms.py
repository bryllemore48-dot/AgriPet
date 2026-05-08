from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from .models import Product, Order, OrderItem, Attendance, UserProfile


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['store', 'name', 'category', 'price_per_kilo', 'stock_in_sacks', 'description', 'image', 'is_active']
        labels = {
            'price_per_kilo': 'Price per Kilo',
            'stock_in_sacks': 'Stock in Sacks',
        }


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'unit_price']


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['store', 'status', 'notes']


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['staff', 'date', 'time_in', 'time_out', 'status', 'notes']


class UserForm(UserChangeForm):
    password = None
    first_name = forms.CharField(label='Name', required=True)

    class Meta:
        model = User
        fields = ['first_name', 'email']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio']
        labels = {
            'avatar': 'Profile Picture',
            'bio': 'About Me',
        }
