# from django.middleware.csrf import CSRFTokenMissing, CSRFTokenNotMatch
from django.http import JsonResponse, HttpResponseRedirect
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from cartapp.models import Cart,CartItem,Wishlist
from orderapp.models import Wallet
from shop.models import Product, Color, Size, UserProfile, ProductVariant, CustomUser, Coupon, CategoryOffer
from django.core.exceptions import ObjectDoesNotExist
from utils.common_utils import calculate_offered_price

# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart



def add_to_cart(request):
    try:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if request.user.is_authenticated:
                # Parse JSON data from the request body
                data = json.loads(request.body.decode('utf-8'))
                product_qty = data['product_qty']
                product_id = data['pid']
                product_color_id = data['color']
                product_size_id = data['size']

                # Retrieve Color and Size objects based on IDs
                selected_color = get_object_or_404(Color, id=product_color_id)
                selected_size = get_object_or_404(Size, id=product_size_id)

                try:
                    # Attempt to find the matching ProductVariant
                    product_status = ProductVariant.objects.get(product_id=product_id, color=selected_color, size=selected_size)


                except ProductVariant.DoesNotExist:
                    return JsonResponse({'status': 'Product not found'}, status=404)

                if product_status:
                    # Find the user's cart or create one if it doesn't exist
                    cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))

                    # Check if the same item with the exact variations exists in the cart
                    cart_item_exists = CartItem.objects.filter(
                        product=product_status.product,
                        product_variant=product_status,
                        cart=cart,
                        user=request.user,
                        color=selected_color,
                        size=selected_size,
                    ).first()

                    if cart_item_exists:
                        total_quantity = cart_item_exists.quantity + product_qty
                        if total_quantity > product_status.quantity:
                            return JsonResponse({'status': 'Insufficient Stock'}, status=400)
                        else:
                            # Update the quantity to the desired quantity, not just adding
                            cart_item_exists.quantity = product_qty
                            cart_item_exists.save()
                            return JsonResponse({'status': 'Quantity Updated in Cart'}, status=200)

                    else:
                        if product_status.quantity >= product_qty:
                            # Create a new cart item if it doesn't exist
                            CartItem.objects.create(
                                product=product_status.product,
                                product_variant=product_status,
                                quantity=product_qty,
                                cart=cart,
                                user=request.user,
                                color=selected_color,
                                size=selected_size,
                            )
                            return JsonResponse({'status': 'Product Added to Cart'}, status=200)
                        else:
                            return JsonResponse({'status': 'Product Stock Not Available'}, status=200)
                else:
                    return JsonResponse({'status': 'Product not found'}, status=404)
            else:
                 return JsonResponse({'status': 'Login to Add Cart', 'redirect': '/shop/login/'}, status=200)


        else:
            return JsonResponse({'status': 'Invalid Access'}, status=200)
    except Exception as e:
        return JsonResponse({'status': 'Error: {}'.format(str(e))}, status=500)

# @login_required(login_url = 'shop:login')
def update_cart(request, product_id):
    try:


        product = get_object_or_404(Product, id=product_id)

        selected_color_id = request.POST.get('color')
        selected_size_id = request.POST.get('size')

        selected_color_id = int(selected_color_id)
        selected_size_id = int(selected_size_id)
        try:
            selected_color = Color.objects.get(id=selected_color_id)
            selected_size = Size.objects.get(id=selected_size_id)
        except (Color.DoesNotExist, Size.DoesNotExist):
            selected_color = None
            selected_size = None

        selected_product_variant = ProductVariant.objects.get(
            product=product,
            color=selected_color,
            size=selected_size
        )


        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Find the user's cart or create one if it doesn't exist
            cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))
        else:

            cart_id = _cart_id(request)

            cart, created = Cart.objects.get_or_create(cart_id=cart_id)



        cart_items = CartItem.objects.filter(
            product=product,
            product_variant=selected_product_variant,
            cart=cart,
            user=request.user,
            color=selected_color,
            size=selected_size,
        )



        # Check if the cart item with the exact same variations exists
        if cart_items.exists():

            try:

                cart_item = cart_items.first()

                if cart_item.quantity < selected_product_variant.quantity:
                    cart_item.quantity += 1

                    cart_item.save()

                else:
                    messages.warning(request, 'Sorry, the selected quantity exceeds the available stock.')
                    # return JsonResponse({'status': 'Sorry, the selected quantity exceeds the available stock.'}, status=200)
            except Exception as e:
               pass
        else:


            CartItem.objects.create(
                product=product,
                product_variant=selected_product_variant,
                quantity=1,
                cart=cart,
                user=request.user,
                color=selected_color,
                size=selected_size,
            )

        return redirect('cartapp:cart')
    except :
        pass
        # Handle exceptions here
        # return HttpResponse('Error: ' + str(e), status=500)  # Return an error response
# @login_required(login_url='shop:login')
def cart(request, total=0, quantity=0, cart_items=None):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please log in to view your cart.')
        return redirect('shop:login')
    else:
        shipping_charge = 10
        grand_total = 0
        coupon_discount = 0  # Initialize coupon_discount to 0
        discount = 0
        cart = None
        try:

            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(user=request.user, balance=0.0)

        # wallet = Wallet.objects.get(user=request.user)


        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            # Set cart to None if it doesn't exist
            pass

        if cart is not None:
            cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('id')

            for cart_item in cart_items:
                offer_price = calculate_offered_price(cart_item.product)
                total += offer_price * cart_item.quantity
                quantity += cart_item.quantity

            grand_total = total + shipping_charge

        if cart and cart.cartitem_set.count() == 0:
            # Clear the coupon associated with the cart
            cart.coupon = None
            cart.save()



        context = {
            'total': total,
            'quantity': quantity,
            'cart_items': cart_items,
            'shipping_charge': shipping_charge,
            'grand_total': grand_total,
            'cart': cart,
            # 'coupon_discount': coupon_discount,
            'wallet':wallet,
        }
        return render(request, 'cart/cart.html', context)

def remove_coupon(request,cart_id):
    cart=Cart.objects.get(cart_id=_cart_id(request))
    cart.coupon=None
    cart.save()
    messages.success(request,"Coupon Removed")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
def apply_coupon(request, cart_id):

    cart = get_object_or_404(Cart, id=cart_id)
    total=quantity=0
    shipping_charge=10
    if cart is not None:
            cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('id')

            for cart_item in cart_items:
                offer_price = calculate_offered_price(cart_item.product)
                total += offer_price * cart_item.quantity
                quantity += cart_item.quantity

            grand_total = total + shipping_charge


    if request.method == 'POST':
        try:

            coupon_code = request.POST.get('coupon')
            coupon_obj = Coupon.objects.filter(coupon_code__iexact=coupon_code).first()

            if not coupon_code.strip():
                messages.warning(request, "Please enter a coupon code")
            elif coupon_obj is None:
                messages.warning(request, "Invalid Coupon")
            elif cart.coupon:
                messages.warning(request, "Coupon already exists")
            elif grand_total < coupon_obj.minimum_amount:
                messages.warning(request, f"Amount should be greater than {coupon_obj.minimum_amount}")
            elif not coupon_obj.is_available:
                messages.warning(request, "Coupon expired")
            else:
                # Apply the coupon to the cart
                cart.coupon = coupon_obj
                cart.save()
                messages.success(request, "Coupon applied")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        except Coupon.DoesNotExist:
            messages.warning(request, "Invalid Coupon")

    # If the coupon application fails or it's a GET request, redirect to the checkout page
    return redirect('cartapp:checkout')

def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    total = 0

    try:
        if request.user.is_authenticated:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()

            # Calculate the new total after removing the item
            for item in cart.cartitem_set.all():
                total += item.product.price * item.quantity

            if cart.coupon and not total >= cart.coupon.minimum_amount:
                messages.warning(request, f"Amount should be greater than {cart.coupon.minimum_amount}")
                cart.coupon = None
                cart.save()
    except Exception as e:
        pass

    return redirect('cartapp:cart')

def remove_allcart(request,product_id,cart_item_id):
    product=get_object_or_404(Product,id=product_id)
    if request.user.is_authenticated:
        cart_item=CartItem.objects.get(product=product,user=request.user,id=cart_item_id)
    else:

        cart=Cart.objects.get(cart_id=_cart_id(request))
        cart_item=CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
    cart_item.delete()
    return redirect('cartapp:cart')

@login_required(login_url='shop:login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        shipping_charge = 10
        balance_after_wallet = 0
        grand_total = 0
        coupon_discount = 0

        # Initialize wallet outside the if block
        wallet = None

        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
            cart = Cart.objects.get(cart_id=_cart_id(request))

            # Check if the Wallet object exists for the user
            try:
                wallet = Wallet.objects.get(user=request.user)
            except Wallet.DoesNotExist:
                pass

        for cart_item in cart_items:
            product = cart_item.product
            offer_price = calculate_offered_price(cart_item.product)
            total += (offer_price) * cart_item.quantity
            quantity += cart_item.quantity

        tax_amount=total*6/100
        grand_total = total + shipping_charge
        total_with_tax=grand_total+tax_amount
        cart.tax_amount=tax_amount

        if cart.coupon:
            coupon_discount = cart.coupon.discount_price
            total_with_tax=total_with_tax - coupon_discount
            cart.coupon_amount=coupon_discount
        cart.total_with_tax=total_with_tax
        cart.tax_amount=tax_amount

        cart.save()
    except ObjectDoesNotExist:
        pass  # just ignore


    userprofile = UserProfile.objects.get(user=request.user)
    used_amount=0

    cart.is_wallet_used=False
    # Check if wallet is not None before using it
    wallet_amount_present = True

    if request.user.wallet.balance > 0:
        request.session['wallet_amount_present'] = wallet_amount_present
        balance_after_wallet,used_amount = wallet.calculate_after_wallet(total_with_tax)
        cart.is_wallet_used=True

        cart.save()

    # Inside the checkout view

    request.session['balance_after_wallet'] = float(balance_after_wallet)
    request.session['used_amount'] = float(used_amount)

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'shipping_charge': shipping_charge,
        'grand_total': grand_total,
        'userprofile': userprofile,
        'coupon_discount': coupon_discount,
        'cart': cart,
        'wallet': wallet,
        'balance_after_wallet': balance_after_wallet,
        'used_amount':used_amount,
        'tax_amount':tax_amount,
        'total_with_tax':total_with_tax,

    }
    return render(request, 'order/checkout.html', context)


def addToWishlist(request):
    try:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if request.user.is_authenticated:
                # Parse JSON data from the request body
                data = json.loads(request.body.decode('utf-8'))
                product_id = data['pid']
                product_color_id = data['color']
                product_size_id = data['size']


                # Retrieve Color and Size objects based on IDs
                try:
                    selected_color = get_object_or_404(Color, id=product_color_id)
                    selected_size = get_object_or_404(Size, id=product_size_id)
                except Color.DoesNotExist:
                    return JsonResponse({'status': 'Color not found'}, status=404)
                except Size.DoesNotExist:
                    return JsonResponse({'status': 'Size not found'}, status=404)

                try:
                    # Attempt to find the matching ProductVariant
                    product_status = ProductVariant.objects.get(product_id=product_id, color=selected_color, size=selected_size)
                except ProductVariant.DoesNotExist:
                    return JsonResponse({'status': 'error', 'error': 'Product not found'}, status=404)

                # Check if the product is already in the wishlist
                if Wishlist.objects.filter(user=request.user, productvariant=product_status,product_id=product_id).exists():
                    return JsonResponse({'status': 'Already in wishlist'}, status=200)

                else:
                    # Add the product to the wishlist
                   Wishlist.objects.create(
                        user=request.user,
                        productvariant=product_status,
                        product_id=product_id
                    )
                   # messages.success(request, 'Product added to wishlist successfully')
                   return JsonResponse({'status': 'Product added to wishlist successfully'})
    except Exception as e:
        import traceback

        return JsonResponse({'status': 'error', 'error': str(e)})

    # Add this part to handle GET requests
    return JsonResponse({'status': 'error', 'error': 'Invalid request method'})


def view_wishlist(request):

    if not request.user.is_authenticated:
        messages.warning(request, 'Please log in to view your wishlist.')
        return redirect('shop:login')  # Redirect the user to the login page
    else:

        wishlist_items = Wishlist.objects.filter(user=request.user)
        context = {'wishlist_items': wishlist_items}
        return render(request, 'cart/wishlist.html', context)

def remove_wishlist(request, wishlist_item_id):
    wishlist_item = get_object_or_404(Wishlist, id=wishlist_item_id, user=request.user)
    wishlist_item.delete()
    # messages.success(request, 'Item removed from wishlist successfully.')
    return redirect('cartapp:view_wishlist')

def addcart_wishlist(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = 1
        color_id = request.POST.get('color')
        size_id = request.POST.get('size')

        product = get_object_or_404(Product, id=product_id)

        # Find the product variant based on color and size
        product_variant = get_object_or_404(
            ProductVariant,
            product=product,
            color_id=color_id,
            size_id=size_id
        )

        if request.user.is_authenticated:
            # Find the user's cart or create one if it doesn't exist
            cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))

        cart_items = CartItem.objects.filter(
            product=product,
            product_variant=product_variant,
            cart=cart,
            user=request.user,
            color_id=color_id,
            size_id=size_id,
        )
        if cart_items:
            messages.warning(request, 'Product already in cart')
        else:
            # Add the product to the cart
            CartItem.objects.create(
                product=product,
                product_variant=product_variant,
                quantity=1,
                cart=cart,
                user=request.user,
                color_id=color_id,
                size_id=size_id,
            )


            # Remove the product from the wishlist
            Wishlist.objects.filter(
                user=request.user,
                product=product,
                productvariant=product_variant
            ).delete()

            messages.success(request, 'Product added to cart successfully')
            return redirect('cartapp:cart')
    # Redirect to the wishlist page after adding to the cart
    return redirect('cartapp:view_wishlist')
