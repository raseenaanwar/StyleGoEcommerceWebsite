
from django.db import models
from  django.db import models
from shop.models import Product,CustomUser,Color,Size,ProductVariant,Coupon

# Create your models here.
class Cart(models.Model):
    cart_id=models.CharField(max_length=200,blank=True,null=True)
    # user = models.ForeignKey(CustomUser,null=True,blank=True, on_delete=models.CASCADE)
    date_added=models.DateField(auto_now_add=True)
    coupon=models.ForeignKey(Coupon,on_delete=models.SET_NULL,null=True,blank=True)
    tax_amount=models.PositiveIntegerField(default=0)
    total_with_tax=models.FloatField(default=0)
    coupon_amount=models.FloatField(default=0)
    is_wallet_used=models.BooleanField(default=False)


    def __str__(self):
        return self.cart_id

class CartItem(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,null=True)
    quantity=models.PositiveIntegerField(null=False,blank=False)
    # total=models.DecimalField(max_digits=10,decimal_places=2,default=None)
    is_active=models.BooleanField(default=True)

    def __str__(self):
        product_info = f"Product: {self.product}, Variant: {self.product_variant}"
        user_info = f", User: {self.user}" if self.user else ""
        color_info = f", Color: {self.color}" if self.color else ""
        size_info = f", Size: {self.size}" if self.size else ""
        quantity_info = f", Quantity: {self.quantity}"
        active_info = f", Active: {self.is_active}"

        return product_info + user_info + color_info + size_info + quantity_info + active_info

    def sub_total(self):
        offered_price = self.product.calculate_offered_price()
        if self.product.price > offered_price:
            return offered_price * self.quantity
        else:
            return self.product.price * self.quantity
class Wishlist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    productvariant=models.ForeignKey(ProductVariant,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'productvariant')
