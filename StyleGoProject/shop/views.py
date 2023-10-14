import re
from datetime import timezone
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django import forms
from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from utils.common_utils import calculate_offered_price
from .models import UserProfile, Size, RecentlySearched
from orderapp.models import OrderProduct, Wallet
from .forms import UserForm, UserProfileForm
from .utils import TokenGenerator, generate_token
from django.core.mail import EmailMessage, send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.http import HttpResponse
from .models import CustomUser,Category,Product,UserProfile,ShippingAddress,ProductVariant,Color
from cartapp.models import Cart,CartItem,Wishlist
from orderapp.models import Order
from cartapp.views import _cart_id
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage,Paginator,PageNotAnInteger
import requests
def home(request):
    categories=Category.objects.all()
    products=Product.objects.all()
    recent_searches = RecentlySearched.objects.order_by('-product_id', '-timestamp').distinct('product_id')[:6]

    return render(request, 'shop/index.html',{'categories':categories,'products':products,'recent_searches':recent_searches})

def shop_product(request, category_id=None):
    categories = Category.objects.all()
    selected_colors = []
    selected_sizes=[]
    if category_id:
        category = get_object_or_404(Category, id=category_id)

        products = Product.objects.all().filter(category=category)
    else:
        products = Product.objects.all().filter(is_available=True).order_by('-updated_date')

    price_ranges = [(0, 600), (600, 1200), (1200, 1800), (1800, 3400)]

    color_list=Color.objects.all()
    color_counts = ProductVariant.objects.values('color__color_name').annotate(count=Count('color'))
    all_colors_count = sum(color_count['count'] for color_count in color_counts)
    color_choices =  [('All Colors', all_colors_count)]
    all_prices_count =color_counts
    price_range_counts = []

    size_list = Size.objects.all()
    size_counts = ProductVariant.objects.values('size__size_name').annotate(count=Count('size'))

    all_sizes_count = sum(size_count['count'] for size_count in size_counts)
    size_choices = [('All Sizes', all_sizes_count)]

    for size_count in size_counts:
        size_name = size_count['size__size_name']
        count = size_count['count']
        size_choices.append((size_name, count))


    size_counts = ProductVariant.objects.values('size__size_name').annotate(count=Count('size'))
    all_sizes_count = sum(size_count['count'] for size_count in size_counts)
    size_choices = [('All Sizes', all_sizes_count)]


    for size_count in size_counts:
        size_name = size_count['size__size_name']
        count = size_count['count']
        size_choices.append((size_name, count))

    for price_range in price_ranges:
        price_filter = Q(price__range=price_range)
        count = products.filter(price_filter).count()
        price_range_counts.append({'price_range': price_range, 'count': count})

    for color_count in color_counts:
        color_name = color_count['color__color_name']
        count = color_count['count']
        color_choices.append((color_name, count))
    if request.method == 'POST':
        selected_price_ranges = request.POST.getlist('price')
        selected_colors = request.POST.getlist('color')
        selected_sizes = request.POST.getlist('size')

        if 'all' in selected_sizes:
            selected_sizes = [size_choice[0] for size_choice in size_choices]

        if selected_price_ranges:
            price_range_filters = [list(map(int, price.split(','))) for price in selected_price_ranges]
            filtered_products = products.filter(price__range=price_range_filters[0]).order_by('price')
            products = filtered_products
        elif selected_colors:
            color_filter = Q(productvariant__color__color_name__in=selected_colors)
            filtered_products = products.filter(color_filter).order_by('price')
            products = filtered_products
        if 'all' in selected_colors:
            selected_colors = [color_choice[0] for color_choice in color_choices]
        if selected_sizes:
            size_filter = Q(productvariant__size__size_name__in=selected_sizes)
            filtered_products = products.filter(size_filter).order_by('price')
            products = filtered_products


    selected_sort = request.GET.get('sort', 'latest')  # Default to 'latest' if not specified

    if selected_sort == 'price':
        # Sort by price
        products = Product.objects.all().order_by('price')

    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()
    context = {
        'products': paged_products,
        'categories': categories,
        'price_ranges': zip(price_ranges, price_range_counts),
        'filtered_products': filtered_products if 'filtered_products' in locals() else None,
        'color_choices':color_choices,
        'selected_colors':selected_colors,
        'selected_sizes':selected_sizes,
        'size_choices': size_choices,
        'selected_sort': selected_sort,
    }

    return render(request, 'shop/shop_product.html', context)
def product_detail(request, id):
    try:

        products = get_object_or_404(Product, pk=id)
        colors = ProductVariant.objects.filter(product=products).values('color__id', 'color__color_name').distinct()


        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=products).exists()
        category_product = products.category
        related_products = Product.objects.filter(category=category_product).exclude(id=products.id)
        user = request.user
        # Initialize product_variant to None
        product_variant = None
        if request.method == 'POST':
            selected_color_id = request.POST.get('color')
            selected_size_id = request.POST.get('size')
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                if not cart.cartitem_set.exists():
                    # Clear the applied coupon if the cart is empty

                    cart.coupon = None
                    cart.save()

            except Cart.DoesNotExist:
                pass
            # Check if the selected color and size combination exists in ProductVariant and is available
            try:
                product_variant = ProductVariant.objects.get(
                    product=products,
                    color__id=selected_color_id,
                    size__id=selected_size_id,
                    quantity__gte=1
                )
            except ProductVariant.DoesNotExist:
                product_variant = None
            if product_variant:
                # Variant exists and is available, add to cart
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=products,
                    product_variant=product_variant
                )

                if created:
                    cart_item.quantity = 1
                else:
                    cart_item.quantity += 1

                cart_item.save()

                return redirect('cartapp:cart')
            else:
                # Variant doesn't exist or is not available, show an error message
                error_message = "This color and size combination is not available."
                return render(request, 'shop/detail.html', {'products': products, 'error_message': error_message})

        context = {
            'products': products,
            'related_products': related_products,
            'in_cart': in_cart,
            'user': user,
            'product_variant': product_variant,  # Include product_variant in the context
            'colors':colors
        }
        return render(request, 'shop/detail.html', context)
    except Exception as e:
        raise

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def get_available_sizes(request):
    if is_ajax(request=request):
        color_id = request.GET.get('color_id')
        pid=request.GET.get('pid')

        try:
            # Query the available sizes based on the selected color
            sizes = ProductVariant.objects.filter(color_id=color_id,product_id=pid).values('size__id', 'size__size_name').distinct()


            size_data = {str(size['size__id']): size['size__size_name'] for size in sizes}
            return JsonResponse({'sizes': size_data})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    return JsonResponse({'error': 'Invalid request'})

def LoginPage(request):
    if request.user.is_authenticated:
        return redirect('shop:home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)

        if user is not None:

            try:
                # Get the cart for the current user (if authenticated)
                if user.is_authenticated:
                    user_cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))
                else:
                    user_cart = None

                # Get the anonymous cart (identified by session-based cart_id)
                anonymous_cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))

                # If the user is authenticated, clear the anonymous cart
                if user.is_authenticated:
                    anonymous_cart_items = CartItem.objects.filter(cart=anonymous_cart)
                    anonymous_cart_items.delete()

                # Retrieve the product variants for items in the user's cart
                user_cart_variants = [item.product_variant for item in CartItem.objects.filter(cart=user_cart)]

                # Retrieve the cart items for the anonymous user
                anonymous_cart_items = CartItem.objects.filter(cart=anonymous_cart)
                for anonymous_item in anonymous_cart_items:
                    if anonymous_item.product_variant not in user_cart_variants:
                        # Create a new cart item in the user's cart

                        new_cart_item = CartItem(
                            product=anonymous_item.product,
                            product_variant=anonymous_item.product_variant,
                            user=user,
                            color=anonymous_item.color,
                            size=anonymous_item.size,
                            cart=user_cart,
                            quantity=anonymous_item.quantity,
                            is_active=True,
                        )
                        new_cart_item.save()
                    else:
                        # Find the matching cart item in the user's cart

                        matching_item = CartItem.objects.get(
                            cart=user_cart,
                            product_variant=anonymous_item.product_variant,
                        )
                        # Update quantity
                        matching_item.user = user
                        matching_item.quantity += anonymous_item.quantity
                        matching_item.save()



            except :
                pass

            login(request, user)

            # Using request library trying to dynamically redirect the user
            url = request.META.get('HTTP_REFERER')

            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))

                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('shop:home')
        else:
            messages.info(request, 'Incorrect Credentials')

    return render(request, 'shop/login.html')



def SignupPage(request):
    if request.user.is_authenticated:
        return redirect('shop:home')

    if request.method == 'POST':
        user_name = request.POST.get('user_name')
        first_name=request.POST.get('first_name')
        last_name=request.POST.get('last_name')
        email = request.POST.get('email')
        contactno=request.POST.get('contactno')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if CustomUser.objects.filter(email=email).exists():
            messages.info(request,'An account with this email already exists.')
        elif CustomUser.objects.filter(user_name=user_name).exists():
            messages.info(request, 'This username is already taken. Please choose another username.')
        elif CustomUser.objects.filter(contactno=contactno).exists():
             messages.info(request, 'This conatct no is already taken. Please choose another username.')
        elif len(user_name)<4:
            messages.info(request, 'Username should contain minimum four characters')
        elif len(user_name)>10:
            messages.info(request, 'Username can only have upto 10 characters')
        elif first_name.isalpha()==False or last_name.isalpha()==False:
            messages.info(request, 'Name cannot have numbers')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messages.info(request, 'Invalid Email')
        elif contactno.isalpha()==True:
            messages.info(request, 'Phonenumber cannot have letters')
        elif not re.match(r"^\d{10}$",contactno):
            messages.info(request, 'Invalid Phone number')
        elif len(contactno)!=10:
            messages.info(request, 'Invalid Phone number')
        elif contactno[0]==0:
            messages.info(request, 'Invalid Phone number')
        elif int(contactno)<0:
            messages.info(request, 'Phone number cannot be negative value')
        elif len(password1) <6 or len(password2)<6:
            messages.info(request, 'Password must atleast contain 6 characters')

        elif len(password1)>12 or len(password2)>12:
            messages.info(request, 'Password can only have upto 12 characters')
        elif password1!=password2:
            messages.info(request, 'Passwords doesnot match to Confirm password!')

        elif password1 == password2:
            try:
                    user = CustomUser.objects.create_user(first_name=first_name,last_name=last_name,contactno=contactno,email=email, password=password1, user_name=user_name)

                    current_site = get_current_site(request)
                    mail_subject = "Please Activate Your Account"
                    message = render_to_string('shop/emaileverification.html', {
                        'user': user,
                        'domain': current_site,
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'token': generate_token.make_token(user),
                    })
                    to_email = email
                    send_email = EmailMessage(mail_subject, message, to=[to_email])
                    send_email.send()

                    messages.success(request, 'We have sent a confirmation link to your email, Please check it..')
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                    login(request, user)
                    return redirect('shop:home')

            except:
                pass

    return render(request, 'shop/signup.html')


@login_required(login_url = 'login')
def Logoutpage(request):
    logout(request)

    return redirect('shop:home')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        User = get_user_model()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:

        user = None

    if user is not None and generate_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations! Your account is activated.')
        return redirect('shop:login')
    return redirect('shop:signup')
def search(request):
    selected_colors = []
    selected_sizes=[]
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
    if keyword:
        try:
            products = Product.objects.order_by('created_date').filter(Q(description__icontains=keyword )| Q(product_name__icontains=keyword))
            product_count=products.count()
        except:
            products=None

        try:
            recently_searched = RecentlySearched.objects.get(query=keyword)
        except RecentlySearched.MultipleObjectsReturned:
            # If multiple objects are returned, choose the first one or handle them as needed
            recently_searched = RecentlySearched.objects.filter(query=keyword).first()
        except RecentlySearched.DoesNotExist:
          recently_searched = None

        if recently_searched:
    # Update the existing object
            recently_searched.timestamp = timezone.now()
            recently_searched.product = products.first()  # Update with your logic
            recently_searched.save()
        else:
    # Create a new object
            recently_searched = RecentlySearched.objects.create(
                query=keyword,
                product=products.first(),  # Update with your logic
                timestamp=timezone.now()
            )


    price_ranges = [(0, 600), (600, 1200), (1200, 1800), (1800, 3400)]

    color_list=Color.objects.all()
    color_counts = ProductVariant.objects.values('color__color_name').annotate(count=Count('color'))
    all_colors_count = sum(color_count['count'] for color_count in color_counts)
    color_choices =  [('All Colors', all_colors_count)]
    # price_range_counts = [('All Prices', all_colors_count)]
    all_prices_count =color_counts
    price_range_counts = []

    size_list = Size.objects.all()
    size_counts = ProductVariant.objects.values('size__size_name').annotate(count=Count('size'))

    all_sizes_count = sum(size_count['count'] for size_count in size_counts)
    size_choices = [('All Sizes', all_sizes_count)]

    for size_count in size_counts:
        size_name = size_count['size__size_name']
        count = size_count['count']
        size_choices.append((size_name, count))


    size_counts = ProductVariant.objects.values('size__size_name').annotate(count=Count('size'))
    all_sizes_count = sum(size_count['count'] for size_count in size_counts)
    size_choices = [('All Sizes', all_sizes_count)]


    for size_count in size_counts:
        size_name = size_count['size__size_name']
        count = size_count['count']
        size_choices.append((size_name, count))

    for price_range in price_ranges:
        price_filter = Q(price__range=price_range)
        count = products.filter(price_filter).count()
        price_range_counts.append({'price_range': price_range, 'count': count})

    for color_count in color_counts:
        color_name = color_count['color__color_name']
        count = color_count['count']
        color_choices.append((color_name, count))
    if request.method == 'POST':
        selected_price_ranges = request.POST.getlist('price')
        selected_colors = request.POST.getlist('color')
        selected_sizes = request.POST.getlist('size')

        if 'all' in selected_sizes:
            selected_sizes = [size_choice[0] for size_choice in size_choices]

        if selected_price_ranges:
            price_range_filters = [list(map(int, price.split(','))) for price in selected_price_ranges]
            filtered_products = products.filter(price__range=price_range_filters[0]).order_by('price')
            products = filtered_products
        elif selected_colors:
            color_filter = Q(productvariant__color__color_name__in=selected_colors)
            filtered_products = products.filter(color_filter).order_by('price')
            products = filtered_products
        if 'all' in selected_colors:
            selected_colors = [color_choice[0] for color_choice in color_choices]
        if selected_sizes:
            size_filter = Q(productvariant__size__size_name__in=selected_sizes)
            filtered_products = products.filter(size_filter).order_by('price')
            products = filtered_products


    selected_sort = request.GET.get('sort', 'latest')  # Default to 'latest' if not specified

    if selected_sort == 'price':
        # Sort by price
        products = Product.objects.all().order_by('price')


    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()
    context = {
        'products': paged_products,

        'price_ranges': zip(price_ranges, price_range_counts),
        'filtered_products': filtered_products if 'filtered_products' in locals() else None,
        'color_choices':color_choices,
        'selected_colors':selected_colors,
        'selected_sizes':selected_sizes,
        'size_choices': size_choices,
        'selected_sort': selected_sort,
        'product_count':product_count,

    }


    return render(request, "shop/shop_product.html", context)
@login_required(login_url='shop:login')
def user_dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()

    try:
        userprofile = UserProfile.objects.get(user_id=request.user.id)
    except UserProfile.DoesNotExist:
        # Create a UserProfile for the user if it doesn't exist
        userprofile = UserProfile(user=request.user)
        userprofile.save()

    context = {
        'orders_count': orders_count,
        'userprofile': userprofile,
    }
    return render(request, 'shop/user_dashboard.html', context)


@login_required(login_url='shop:login')
def edit_profile(request):
    # Check if the user already has a UserProfile
    userprofile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('shop:edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
     }
    return render(request, 'shop/edit_profile.html', context)

@login_required(login_url='shop:login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = CustomUser.objects.get(user_name__exact=request.user.user_name)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()

                messages.success(request, 'Password updated successfully.')
                return redirect('shop:change_password')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('shop:change_password')
        else:
            messages.error(request, 'Password does not match!')
            return redirect('shop:change_password')
    return render(request, 'shop/change_password.html')


def forget_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        if CustomUser.objects.filter(email=email).exists():
            user = CustomUser.objects.get(email__exact=email)

            # Reset password email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('shop/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('shop:login')
        else:
            messages.error(request, 'Account does not exist!')
            return redirect('shop:forgetPassword')
    return render(request, 'shop/forget_password.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect('shop:reset_password')
    else:
        messages.error(request, 'This link has been expired!')
        return redirect('shop:login')


def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = CustomUser.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('shop:login')
        else:
            messages.error(request, 'Password do not match!')
            return redirect('shop:reset_password')
    else:
        return render(request, 'shop/reset_password.html')

@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    for order in orders:
        order.can_be_canceled = order.status in ['New', 'Accepted']
    payment_method=request.session.get('payment_method')

    context = {
        'orders': orders,'payment_method':payment_method
    }
    return render(request, 'shop/my_orders.html', context)

def order_detail(request, order_id):
    cart=None
    subtotal = 0

    try:
        order = Order.objects.get(order_number=order_id)
    except Order.DoesNotExist:
        raise Http404("Order does not exist")

    order_detail = OrderProduct.objects.filter(order=order)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except:
        pass

    for i in order_detail:
        offer_price = calculate_offered_price(i.product)
        subtotal += offer_price * i.quantity

    if cart and cart.coupon:
        coupon_discount = cart.coupon.discount_price
        subtotal -= coupon_discount
    is_wallet_used=request.session.get('is_used',False)

    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
        'is_wallet_used':is_wallet_used,

    }

    return render(request, 'shop/order_detail.html', context)
def cancel_cod_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status not in ['New', 'Accepted']:
        messages.error(request, 'Cannot cancel order. Invalid order status.')
        return redirect('shop:user_dashboard')
    else:

        order.status = 'Cancelled'
        order.save()

        if order.payment_method.lower() == 'paypal':

            wallet = Wallet.objects.get(user=request.user)
            wallet.balance += Decimal(order.total_with_tax)
            # added this
            wallet.is_used=False
            wallet.save()



    order_products = OrderProduct.objects.filter(order=order)
    for order_product in order_products:
        product_variant=ProductVariant.objects.filter(
                product = order_product.product,
                color=order_product.color,
                size=order_product.size,
            ).first()
        if product_variant:
            product_variant.quantity += order_product.quantity
            product_variant.save()
    return render(request,'shop/user_dashboard.html')

def isValidVariant(product,selected_color_id, selected_size_id):
    # Check if the combination of selected color and size exists in ProductVariant
    return ProductVariant.objects.filter(
        product=product,
        colors__id=selected_color_id,
        sizes__id=selected_size_id
    ).exists()
@login_required
def my_wallet(request):
    user=request.user
    user_wallet, created = Wallet.objects.get_or_create(user=user, defaults={'balance': 0.0})

    return render(request, 'shop/my_wallet.html', {'user_wallet': user_wallet})


