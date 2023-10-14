
from django.urls import path,include
from customadminapp import views
from django.contrib import admin
app_name = 'customadminapp'
urlpatterns = [
    path("",views.adminsignin,name="admin_signin"),
    path('dashboard/',views.adminDashboard,name='adminDashboard'),
    path('manage_user',views.manage_user,name='manage_user'),
    path("adminsignout/",views.admin_signout,name="admin_signout"),
    path("blockuser/<int:someid>",views.blockuser,name="blockuser"),
    path("unblockuser/<int:someid>",views.unblockuser,name="unblockuser"),
    path("categories/",views.categories,name="categories"),
    path("add_category/",views.add_category,name="add_category"),
    path("update_category/<int:id>",views.update_category,name="update_category"),
    path('delete_category/<int:id>',views.delete_category,name='delete_category'),
    path("products/",views.products,name="products"),
    path("add_products/",views.add_products,name="add_products"),
    path("update_product/<int:id>",views.update_product,name="update_product"),
    path("delete_product/<int:id>",views.delete_product,name="delete_product"),
    path('manage_order',views.manage_order,name='manage_order'),
    path('orders/update_status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('manage_coupon/',views.manage_coupon,name='manage_coupon'),
    path('add_coupon/',views.add_coupon,name='add_coupon'),
    path('update_coupon/<int:id>/',views.update_coupon,name='update_coupon'),
    path("blockcoupon/<int:id>",views.blockcoupon,name="blockcoupon"),
    path("unblockcoupon/<int:id>",views.unblockcoupon,name="unblockcoupon"),
    path('manage_offer/',views.manage_offer,name='manage_offer'),
    path('add_offer/',views.add_offer,name='add_offer'),
    path('update_offer/<int:id>/',views.update_offer,name='update_offer'),
    path('manage_product_offer/',views.manage_product_offer,name='manage_product_offer'),
    path('add_product_offer/',views.add_product_offer,name='add_product_offer'),
    path('update_product_offer/<int:id>/',views.update_product_offer,name='update_product_offer'),
    path('sales_report/',views.sales_report,name='sales_report'),
    path('download_invoice_pdf/',views.download_invoice_pdf,name='download_invoice_pdf'),
    path('download_invoice_excel/',views.download_invoice_excel,name='download_invoice_excel')
]
