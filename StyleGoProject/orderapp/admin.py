from django.contrib import admin
from .models import Order, OrderProduct, Payment, Wallet

# Register your models here.

admin.site.register(OrderProduct)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'contactno', 'email', 'city', 'order_total', 'shipping_charge', 'status', 'is_ordered', 'created_at']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'first_name', 'last_name', 'contactno', 'email']
    list_per_page = 20
    # inlines = [OrderProductInline]
admin.site.register(Order,OrderAdmin)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'payment_id', 'payment_method', 'status']

admin.site.register(Payment,PaymentAdmin)
admin.site.register(Wallet)
