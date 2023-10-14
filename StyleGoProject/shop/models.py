from decimal import Decimal

from django.utils.text import slugify

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.urls import reverse


class CustomUserManager(BaseUserManager):
    def create_user(self, first_name,last_name,user_name,email,contactno, password=None):
        if not email:
            raise ValueError('The Email field must be set')
        if not user_name:
            raise ValueError('User must have an username')
        user=self.model(
            email=self.normalize_email(email),
            user_name=user_name,
            first_name=first_name,
            last_name=last_name,
            contactno=contactno,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
class CustomUser(AbstractBaseUser):

    user_name = models.CharField(max_length=50,unique=True)
    first_name=models.CharField(max_length=50)
    last_name=models.CharField(max_length=100)
    email = models.EmailField(max_length=100,unique=True)
    password = models.CharField(max_length=100)
    # company_name = models.CharField(max_length=50, blank=True, null=True)
    contactno = models.IntegerField(blank=True, null=True)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_admin=models.BooleanField(default=False)
    is_superuser=models.BooleanField(default=False)
    last_login = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_name','first_name','last_name']

    class Meta:
        app_label = 'shop'

    def __str__(self):
        return self.user_name

    def has_perm(self,perm,obj=None):
        return self.is_admin
    def has_module_perms(self,shop):
        return True

class Category(models.Model):
    category_name = models.CharField(max_length=100)
    # slug = models.SlugField(unique=True, max_length=150)
    category_desc=models.TextField()
    category_image = models.ImageField(upload_to='images/category/', blank=True, null=True)
    created_date = models.DateField(auto_now_add=True)
    updated_date = models.DateField(auto_now=True)

    class Meta():
        ordering=('category_name',)
        verbose_name='category'
        verbose_name_plural='categories'
    def __str__(self):
        return self.category_name

class Product(models.Model):
    product_name = models.CharField(max_length=200)
    # slug=models.SlugField(max_length=200,unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_date = models.DateField(auto_now_add=True)
    updated_date = models.DateField(auto_now=True)
    is_available=models.BooleanField(default=True)


    def calculate_offered_price(self):

        try:
            product_offer=ProductOffer.objects.get(product=self)
            category_offer = CategoryOffer.objects.get(category=self.category)
            if category_offer.discount_value>product_offer.discount_value:
                discount_amount = category_offer.discount_value
            else:
                discount_amount=product_offer.discount_value

            return self.price - discount_amount

        except ProductOffer.DoesNotExist or CategoryOffer.DoesNotExist:

            return self.price
    def get_unique_colors(self):
        return self.productvariant_set.values('color__id', 'color__color_name').distinct()

    def get_unique_sizes(self):
        return self.productvariant_set.values('size__id', 'size__size_name').distinct()


    class Meta:

        ordering=('product_name',)
        verbose_name='product'
        verbose_name_plural='products'
    def __str__(self):
        return self.product_name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='images/product/', blank=True, null=True)

    def __str__(self):
        return f"Image for {self.product.product_name}"

class Color(models.Model):
    color_name = models.CharField(max_length=50)

    def __str__(self):
        return self.color_name

class Size(models.Model):
    size_name = models.CharField(max_length=50)

    def __str__(self):
        return self.size_name

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)

    quantity = models.PositiveIntegerField(null=True)
    created_date = models.DateField(auto_now_add=True)
    updated_date = models.DateField(auto_now=True)
    is_available=models.BooleanField(default=True)


    def __str__(self):
        return f"{self.product.product_name} - Color: {self.color.color_name}"
class UserProfile(models.Model):
    user=models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='images/user/', blank=True, null=True)

    country=models.CharField(max_length=200)
    state=models.CharField(max_length=200)
    city=models.CharField(max_length=200)
    address_line_1=models.CharField(max_length=200)
    address_line_2=models.CharField(max_length=200)
    pincode=models.PositiveIntegerField(blank=True, null=True, default=None)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):

           return f"Product: {self.product.product_name}, Size: {self.size.size_name}, Color: {self.color.color_name}, Quantity: {self.quantity}"


class ShippingAddress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='shipping_addresses')
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)
    contactno = models.PositiveIntegerField()
    country = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    address_line_1 = models.CharField(max_length=200)
    address_line_2 = models.CharField(max_length=200)
    pincode = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.username}"


class Coupon(models.Model):
    coupon_code=models.CharField(max_length=15)
    is_available=models.BooleanField(default=False)
    discount_price=models.IntegerField(default=100)
    minimum_amount=models.IntegerField(default=1000)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)

class CategoryOffer(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    is_available=models.BooleanField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)

class ProductOffer(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    is_available=models.BooleanField()
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)


class RecentlySearched(models.Model):

    query = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f' {self.query}'

