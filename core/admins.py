from django.contrib import admin
from .models import Product, Client, Order, OrderItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name']

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'area', 'created_at']
    search_fields = ['name', 'phone']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'total_amount', 'delivery_mode', 'status', 'created_at']
    list_filter = ['status', 'delivery_mode', 'created_at']
    inlines = [OrderItemInline]


@admin.register(Category)
