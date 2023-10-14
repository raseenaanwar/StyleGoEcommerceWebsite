import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string, get_template
from django.views.decorators.cache import never_cache, cache_control
from utils.common_utils import calculate_offered_price
from io import  BytesIO
from cartapp.models import CartItem, Cart
from cartapp.views import _cart_id, cart
from shop.models import UserProfile, CustomUser, ShippingAddress, ProductVariant, CategoryOffer
from .forms import Orderform
from .models import Order, OrderProduct, Product, Payment,Wallet
from .utils import get_product_variant_for_order
import json
from xhtml2pdf import pisa
import uuid

@never_cache
def place_order(request,total=0,quantity=0):
    current_user=request.user
    cart= Cart.objects.get(cart_id=_cart_id(request))
    balance_after_wallet = Decimal(request.session.get('balance_after_wallet', 0))
    used_amount = Decimal(request.session.get('used_amount', 0))
    coupon_discount=0
    cart_items=CartItem.objects.filter(user=current_user)
    cart_count=cart_items.count()
    if cart_count<=0:
        return redirect('shop:home')
    grand_total = 0
    shipping_charge = 10

    temp=None

    for cart_item in cart_items:
            offer_price = calculate_offered_price(cart_item.product)
            total += (offer_price) * cart_item.quantity
            quantity += cart_item.quantity
    # order.tax_amount=total*5/100
    # grand_total = total + shipping_charge
    # if cart.coupon:
    #     coupon_discount=cart.coupon.discount_price
    #     grand_total=grand_total-coupon_discount
    # temp=grand_total

    if request.method=='POST':

        form=Orderform(request.POST)
        if form.is_valid():
            payment_method=request.POST.get('payment-method')

            if payment_method is None:
                form.add_error(None,'Please select a payment method')
            else:

                data=Order()
                data.user = current_user
                data.first_name = form.cleaned_data['first_name']
                data.last_name = form.cleaned_data['last_name']
                data.contactno = form.cleaned_data['contactno']
                data.email = form.cleaned_data['email']
                data.address_line_1 = form.cleaned_data['address_line_1']
                data.address_line_2 = form.cleaned_data['address_line_2']
                data.country = form.cleaned_data['country']
                data.state = form.cleaned_data['state']
                data.city = form.cleaned_data['city']
                data.pincode=form.cleaned_data['pincode']
                data.order_total = grand_total
                data.shipping_charge = shipping_charge
                data.coupon_discount=coupon_discount
                data.ip = request.META.get('REMOTE_ADDR')

                data.save()
                d = datetime.date.today()
                year=d.year
                month=d.month
                date=d.day
                d = datetime.date(year,month,date)
                current_date = d.strftime("%Y%m%d")
                order_number = current_date + str(data.id)
                data.order_number = order_number
                data.save()
                shipping_address=None
                if request.POST.get('shipto'):
                    shipping_address = ShippingAddress(
                    user=current_user,
                    first_name=form.cleaned_data['shipping_first_name'],
                    last_name=form.cleaned_data['shipping_last_name'],
                    contactno=form.cleaned_data['shipping_contactno'],
                    email=form.cleaned_data['shipping_email'],
                    address_line_1=form.cleaned_data['shipping_address_line_1'],
                    address_line_2=form.cleaned_data['shipping_address_line_2'],
                    country=form.cleaned_data['shipping_country'],
                    state=form.cleaned_data['shipping_state'],
                    city=form.cleaned_data['shipping_city'],
                    pincode=form.cleaned_data['shipping_pincode']
                            )

                    if form.is_valid():
                        shipping_address.save()
                order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
                order.shipping_address = shipping_address
                order.tax_amount=cart.tax_amount
                order.total_with_tax=cart.total_with_tax
                order.is_wallet_used=cart.is_wallet_used
                order.save()
                grand_total = order.total_with_tax + shipping_charge
                if cart.coupon:
                    coupon_discount=cart.coupon.discount_price
                    grand_total=grand_total-coupon_discount
                temp=grand_total
                # order.total_with_tax=grand_total+order.tax_amount
                order.save()

                wallet = get_object_or_404(Wallet, user=request.user)

                if order.is_wallet_used:
                    order.extra_paid= round(balance_after_wallet, 2)
                    order.wallet_amount_used = used_amount
                    grand_total=balance_after_wallet
                    order.is_wallet_used=True

                    order.save()
                    wallet.balance -= used_amount


                    wallet.save()
                else:

                    grand_total=temp
                if order.is_wallet_used:
                    grand_total=order.extra_paid
                else:
                    grand_total=order.total_with_tax
                wallet_amount_present = request.session.get('wallet_amount_present', False)

                if payment_method=='paypal':
                    # request.session['payment_method']='paypal'
                    order.payment_method='paypal'
                    order.save()
                    if order.extra_paid != 0:
                        grand_total=order.extra_paid
                        wallet.is_used=True
                        wallet.save()
                    else:
                        grand_total=order.total_with_tax


                    context = {
                        'order': order,
                        'cart_items': cart_items,
                        'total': total,
                        'shipping_charge': shipping_charge,
                        'grand_total': grand_total,
                        'coupon_discount':coupon_discount,
                        'cart':cart,
                        'wallet':wallet,
                        'wallet_amount_present':wallet_amount_present

                    }
                    return render(request, 'order/paypal_payments.html', context)
                elif payment_method=='cod':
                    order.payment_method='cod'
                    order.save()

                    # request.session['payment_method']='cod'
                    context = {
                        'order': order,
                        'cart_items': cart_items,
                        'total': total,
                        'shipping_charge': shipping_charge,
                        'grand_total': grand_total,
                        'coupon_discount':coupon_discount,
                        'cart':cart,
                        'wallet':wallet,
                        'wallet_amount_present':wallet_amount_present
                    }
                    return render(request, 'order/cod_payments.html', context)


    else:
        form=Orderform()
        context = {
                'form':form,
                'cart_items': cart_items,
                'total': total,
                'shipping_charge': shipping_charge,
                'grand_total': grand_total,
                'coupon_discount':coupon_discount,
                'cart':cart

            }
        return render(request, 'order/checkout.html',context)
    return HttpResponse("Something went wrong")
@never_cache
def confirm_order(request,order_id):
    try:
        discount=coupon_discount=0
        # order = Order.objects.get(user=request.user, is_ordered=False)
        order = Order.objects.get(id=order_id, user=request.user, is_ordered=False)
        cart= Cart.objects.get(cart_id=_cart_id(request))

        order.is_ordered = True
        order.save()

        # Transfer cart items to order products
        cart_items = CartItem.objects.filter(user=request.user)
        for cart_item in cart_items:
            order_product = OrderProduct()
            order_product.order_id = order.id
            order_product.user_id = request.user.id
            order_product.product_id = cart_item.product_id
            order_product.quantity = cart_item.quantity
            order_product.product_price = cart_item.product.price
            order_product.ordered = True
            order_product.color=cart_item.color
            order_product.size=cart_item.size
            order_product.save()

            # Transfer variations
            cart_item = CartItem.objects.get(id=cart_item.id)
            selected_color = cart_item.color
            selected_size = cart_item.size

            order_product = OrderProduct.objects.get(id=order_product.id)
            # order_product.variations.set(product_variations)
            order_product.save()
            product_variant=ProductVariant.objects.get(
                product=cart_item.product,
                color=selected_color,
                size=selected_size,

            )
            product_variant.quantity-=cart_item.quantity
            product_variant.save()
        # Clear cart items
        CartItem.objects.filter(user=request.user).delete()
        is_wallet_used=request.session.get('is_used',False)

        # Send order confirmation email
        mail_subject = "Your order placed successfully"
        message = render_to_string('order/orderemail.html', {
            'user': request.user,
            'order': order,
        })
        to_email = request.user.email
        send_email = EmailMessage(mail_subject, message, to=[to_email])
        send_email.send()
        subtotal=0
        quantity=0
        try:
            ordered_products = OrderProduct.objects.filter(order_id=order.id)
            for cart_item in cart_items:
                product = cart_item.product
                offer_price = calculate_offered_price(cart_item.product)
                subtotal += (offer_price) * cart_item.quantity
                quantity += cart_item.quantity
            if cart.coupon:
                coupon_discount=cart.coupon.discount_price
                subtotal-=coupon_discount

            grand_total=order.total_with_tax
            context = {
                'order': order,
                'ordered_products': ordered_products,
                'order_number': order.order_number,
                'subtotal': subtotal,
                'cart':cart,
                'coupon_discount':coupon_discount,
                'is_wallet_used':is_wallet_used,
                'grand_total':grand_total
            }
            return render(request, 'order/confirm_order.html', context)

        except Order.DoesNotExist:
            return redirect('shop:home')

        return render(request, 'order/confirm_order.html', context)

    except Order.DoesNotExist:
        return redirect('orderapp:no_order_found')

@never_cache
def no_order_found(request):
    return render(request,'order/no_order_found.html')
@never_cache
def cod_payments(request):
    return render(request,'order/cod_payments.html')
@never_cache
def paypal_payments(request):

    try:
        body = json.loads(request.body)
        order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])
        # Store transaction details inside Payment model
        payment = Payment(
            user = request.user,
            payment_id = body['transID'],
            payment_method = body['payment_method'],
            amount_paid = order.total_with_tax,
            status = body['status'],
        )
        payment.save()
        order.payment = payment
        order.is_ordered = True
        order.save()

        # Move the cart items to Order Product table
        cart_items = CartItem.objects.filter(user=request.user)

        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.payment = payment
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.color=item.color
            orderproduct.size=item.size
            orderproduct.save()

            cart_item = CartItem.objects.get(id=item.id)
            orderproduct = OrderProduct.objects.get(id=orderproduct.id)
            orderproduct.save()

            try:
                # Reduce the quantity of the sold products
                product_variant=ProductVariant.objects.get(
                        product=cart_item.product,
                        color__color_name=item.color.color_name,  # Match color name
                        size__size_name=item.size.size_name,  # Match size name


                    )
                product_variant.quantity-=cart_item.quantity
                product_variant.save()
            except ProductVariant.DoesNotExist:
                pass

        # Clear cart
        CartItem.objects.filter(user=request.user).delete()

        mail_subject = 'Thank you for your order!'
        message = render_to_string('order/orderemail.html', {
            'user': request.user,
            'order': order,
        })
        to_email = request.user.email
        send_email = EmailMessage(mail_subject, message, to=[to_email])
        send_email.send()

        # Send order number and transaction id back to sendData method via JsonResponse
        data = {
            'order_number': order.order_number,
            'transID': payment.payment_id,
        }
        return JsonResponse(data)
    except Order.DoesNotExist:
        return redirect('orderapp:no_order_found')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        cart = Cart.objects.get(cart_id=_cart_id(request))
        subtotal = 0
        for i in ordered_products:
            offer_price = calculate_offered_price(i.product)
            subtotal +=offer_price * i.quantity
        if cart.coupon:
            coupon_discount=cart.coupon.discount_price
            subtotal=subtotal-coupon_discount

        payment = Payment.objects.get(payment_id=transID)
        cart.coupon = None
        cart.save()
        is_wallet_used=order.is_wallet_used
        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
            'cart':cart,
            'coupon_discount':coupon_discount,
            'is_wallet_used':is_wallet_used,
        }
        return render(request, 'order/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('shop:home')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def paypal_order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
    coupon_discount=0
    cart = Cart.objects.get(cart_id=_cart_id(request))
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            offer_price = calculate_offered_price(i.product)
            subtotal +=offer_price * i.quantity
        if cart.coupon:
            coupon_discount=cart.coupon.discount_price
            subtotal=subtotal-coupon_discount
        is_wallet_used=order.is_wallet_used
        payment = Payment.objects.get(payment_id=transID)
        cart.coupon = None
        cart.save()
        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
            'cart':cart,
            'coupon_discount':coupon_discount,
            'is_wallet_used':is_wallet_used
        }
        return render(request, 'order/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('shop:home')

def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    transID = request.GET.get('payment_id')
    coupon_discount = 0
    cart = Cart.objects.get(cart_id=_cart_id(request))

    try:
        order_number =order.order_number
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            offer_price = calculate_offered_price(i.product)
            subtotal += offer_price * i.quantity

        if cart.coupon:
            coupon_discount = cart.coupon.discount_price
            subtotal = subtotal - coupon_discount

        try:
            payment = Payment.objects.get(payment_id=transID)
        except Payment.DoesNotExist:
            # Handle the case where payment is not found (e.g., COD order)
            payment = None
        is_wallet_used=order.is_wallet_used
        template_path = 'order/invoice.html'  # Provide the correct path to your HTML template
        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': order.payment.payment_id if order.payment else None,
            'payment': payment,
            'subtotal': subtotal,
            'cart': cart,
            'coupon_discount': coupon_discount,
             'is_wallet_used':is_wallet_used,
                     }

        # Render the template
        template = get_template(template_path)
        html = template.render(context)
        # Create a PDF file
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=invoice_{order.order_number}.pdf'

        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')

        return response
    except Exception as e:
        return HttpResponse(f'Error: {e}')

