from django.urls import path,include
from cartapp import views

app_name = 'cartapp'
urlpatterns = [
    # path("",views.adminsignin,name="admin_signin"),
    path('',views.cart,name='cart'),
    path('add_to_cart/',views.add_to_cart,name='add_to_cart'),
    path('update_cart/<int:product_id>',views.update_cart,name='update_cart'),
    path('remove_cart/<int:product_id>/<int:cart_item_id>/',views.remove_cart,name='remove_cart'),
    path('remove_allcart/<int:product_id>/<int:cart_item_id>/',views.remove_allcart,name='remove_allcart'),
    path('checkout/',views.checkout,name='checkout'),
    path('addToWishlist/', views.addToWishlist, name='addToWishlist'),
    path('view_wishlist/',views.view_wishlist,name='view_wishlist'),
    path('remove_wishlist/<int:wishlist_item_id>',views.remove_wishlist,name='remove_wishlist'),
    path('remove_coupon/<cart_id>/',views.remove_coupon,name='remove_coupon'),
    path('addcart_wishlist/',views.addcart_wishlist,name='addcart_wishlist'),
    path('apply_coupon/<cart_id>/',views.apply_coupon,name='apply_coupon'),

]
