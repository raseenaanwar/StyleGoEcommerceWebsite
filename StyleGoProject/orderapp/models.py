from django.db import models
from shop.models import CustomUser,Product,Color,Size,ShippingAddress
from django.core.validators import MinValueValidator
# Create your models here.
class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, validators=[MinValueValidator(0)])
    is_used=models.BooleanField(default=False)
    final_price_to_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)


    def calculate_after_wallet(self, order_amt):
        try:
            used_amt = 0
            if self.balance > 0:
                if self.balance >= order_amt:
                    print('self.balance >= order_amt')
                    self.final_price_to_pay = 0
                    used_amt = order_amt
                    self.balance -= order_amt
                else:
                    print(' esle self.balance >= order_amt')
                    self.final_price_to_pay = order_amt - self.balance
                    used_amt = self.balance
                    self.balance = 0

                self.is_used = True

            else:
                # Handle the case where the balance is already zero or negative
                self.final_price_to_pay = order_amt
            print('finnal',self.final_price_to_pay)
            print('used',used_amt)
            return self.final_price_to_pay, used_amt

        except Order.DoesNotExist:
            # Handle the case where the order doesn't exist
            pass
        except Exception as e:
            # Handle other exceptions
            print(f"An error occurred: {e}")
            return self.final_price_to_pay, used_amt

class Payment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100) # this is the total amount paid
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    # new field to indicate whether the payment is from the wallet
    is_wallet_payment = models.BooleanField(default=False)

    def __str__(self):
        return self.payment_id

class Order(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    contactno = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=50)
    address_line_2 = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    pincode=models.PositiveIntegerField()
    payment_method = models.CharField(max_length=100, default='cod')
    order_total = models.FloatField()
    shipping_charge= models.FloatField(default=None)
    status = models.CharField(max_length=10, choices=STATUS, default='New')
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, blank=True, null=True)
    wallet_amount_used=models.FloatField(default=0)
    extra_paid=models.FloatField(default=0)
    is_wallet_used=models.BooleanField(default=False)
    tax_amount=models.PositiveIntegerField(default=0)
    total_with_tax=models.FloatField(default=0)
    coupon_amount=models.FloatField(default=0)
    is_coupon_used=models.BooleanField(default=False)
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'

    def __str__(self):
        return self.first_name


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, blank=True, null=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, blank=True, null=True)

    # variations = models.ManyToManyField(Variation, blank=True)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
     # new field to indicate whether the product was purchased using the wallet
    is_wallet_purchase = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, blank=True, null=True)
    def __str__(self):
        return self.product.product_name

