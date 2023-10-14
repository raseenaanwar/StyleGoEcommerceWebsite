
from django.urls import path,include
from shop import views
from django.contrib import admin

app_name = 'shop'
urlpatterns = [

    path('',views.home,name='home'),
    path('login/',views.LoginPage,name='login'),
    path('signup/',views.SignupPage,name='signup'),
    path('logout/',views.Logoutpage,name='logout'),
    path('activate/<str:uidb64>/<str:token>/',views.activate,name='activate'),
    path('shop_product/category/<int:category_id>/', views.shop_product, name='shop_product_by_category'),
    path('shop_product/', views.shop_product, name='shop_product'),
    path('product_detail/<int:id>/',views.product_detail,name='product_detail'),
    path('search/',views.search,name='search'),
    path('user_dashboard/',views.user_dashboard,name='user_dashboard'),
    path('edit_profile/',views.edit_profile,name='edit_profile'),
    path('change_password/',views.change_password,name='change_password'),
    path('forget_password/',views.forget_password,name='forget_password'),
    path('reset_password/',views.reset_password,name='reset_password'),
    path('resetpassword_validate/<uidb64>/<token>/', views.resetpassword_validate, name='resetpassword_validate'),
    path('my_orders/',views.my_orders,name='my_orders'),
    path('order_detail/<int:order_id>/',views.order_detail,name='order_detail'),
    path('cancel_cod_order/<int:order_id>/',views.cancel_cod_order,name='cancel_cod_order'),
    path('get_available_sizes/', views.get_available_sizes, name='get_available_sizes'),
    path('my_wallet/',views.my_wallet,name='my_wallet'),



]
