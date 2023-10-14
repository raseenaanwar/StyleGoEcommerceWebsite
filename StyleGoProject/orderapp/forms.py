from django import forms
from .models import Order
class Orderform(forms.ModelForm):
    class Meta:
        model=Order
        fields=['first_name','last_name','contactno','email','address_line_1','address_line_2','country','state','city','pincode']
