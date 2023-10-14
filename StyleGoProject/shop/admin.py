from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.forms import forms
from django.utils.html import format_html
from django.utils.text import slugify
from .models import CustomUser,Category,Product,UserProfile,Color,Size,ProductVariant,ProductImage,Coupon,CategoryOffer,ProductOffer,ShippingAddress,RecentlySearched


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'first_name', 'last_login', 'date_joined', 'is_active')
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()
    # readonly_fields=('user_name',)


    ordering = ('email',)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'user_name', 'first_name', 'last_name','contactno', 'password1', 'password2'),
        }),
    )

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ( 'user', 'city', 'state', 'country')


class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'price', 'category_name', 'is_available']
    list_editable = ['price',  'is_available']
    list_per_page = 20

    def category_name(self,obj):
        return obj.category.category_name

    category_name.short_description = 'Category'
admin.site.register(Product, ProductAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name']

admin.site.register(Category,CategoryAdmin)
admin.site.register(CustomUser,CustomUserAdmin)
admin.site.register(UserProfile,UserProfileAdmin)
admin.site.register(Size)
admin.site.register(Color)
admin.site.register(ProductVariant)
admin.site.register(ProductImage)
admin.site.register(Coupon)
admin.site.register(CategoryOffer)
admin.site.register(ProductOffer)
admin.site.register(ShippingAddress)

admin.site.register(RecentlySearched)

