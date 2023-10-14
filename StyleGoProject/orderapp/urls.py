from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path,include
from shop import views
from orderapp import views
app_name = 'orderapp'
urlpatterns = [

    path('place_order/',views.place_order,name='place_order'),
    path('confirm_order/<int:order_id>/',views.confirm_order,name='confirm_order'),
    path('paypal_payments/',views.paypal_payments,name='paypal_payments'),
    path('cod_payments/',views.cod_payments,name='cod_payments'),
    path('no_order_found/',views.no_order_found,name='no_order_found'),
    path('order_complete',views.order_complete,name='order_complete'),
    path('paypal_order_complete',views.paypal_order_complete,name='paypal_order_complete'),
    path('download_invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),




]
