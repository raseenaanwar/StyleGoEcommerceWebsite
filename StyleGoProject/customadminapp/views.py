import uuid
import io
import pandas as pd
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
import os
import re
from datetime import datetime, date
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache, cache_control
from xhtml2pdf import pisa
from shop.models import CustomUser, Category, Product, ProductImage,Coupon,CategoryOffer,ProductOffer
from orderapp.models import Order,OrderProduct
from orderapp.models import Order
# Create your views here.

@never_cache
def adminsignin(request):
    if request.user.is_authenticated:

        return redirect('shop:home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)

        if user is not None and user.is_superuser:
            login(request, user)  # Log the user in


            return redirect('customadminapp:adminDashboard')  # Redirect to admin dashboard
        else:
            messages.error(request, 'Incorrect Credentials')

    return render(request, 'admin/adminsignin.html')

@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def adminDashboard(request):

    products = Product.objects.annotate(total_quantity=Sum('productvariant__quantity'))
    total_product=Product.objects.all().count()
    productsale = Product.objects.annotate(total_sales=Sum('orderproduct__order__total_with_tax'))
    user = CustomUser.objects.all()
    orders = Order.objects.exclude(status='cancelled')

    order_count = orders.count()
    user_count = user.count()  # Corrected assignment
    context = {'products': products, 'orders': orders, 'productsale': productsale, 'order_count': order_count, 'user_count': user_count, "total_product":total_product}
    return render(request, 'admin/dashboard.html',context)

# @never_cache
def manage_user(request):



        datas=CustomUser.objects.exclude(is_superuser=True)
        return render(request,"admin/userPage.html",{"datas":datas})

@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def blockuser(request,someid):

    obj=CustomUser.objects.get(id=someid)
    obj.is_active=False
    obj.save()
    return redirect('customadminapp:manage_user')

@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def unblockuser(request,someid):


    obj=CustomUser.objects.get(id=someid)
    obj.is_active=True
    obj.save()
    return redirect('customadminapp:manage_user')

@never_cache
def categories(request):
    # if "is_admin" in request.session:
        datas=Category.objects.all()

        return render(request,"admin/categories.html",{"datas":datas})

#
@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def add_category(request):
    # datas = Category.objects.all()
    if request.method == "POST":
        category_name = request.POST.get("category_name")
        category_desc = request.POST.get("category_desc")
        category_image = request.FILES.get("category_image")
        error={}
        if Category.objects.filter(category_name=category_name).exists():
            messages.error(request, "Same Category name is not allowed")
            return redirect('customadminapp:add_category')
        else:
            new_category = Category(category_name=category_name, category_desc=category_desc, category_image=category_image)
            new_category.save()
            return redirect('customadminapp:categories')
        return render(request, "admin/categories.html")

    return render(request, "admin/categories.html")
@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def update_category(request, id):

    obj = Category.objects.get(id=id)


    if request.method == "POST":
        category_name = request.POST.get("category_name")
        category_desc = request.POST.get("category_desc")
        obj.category_name = category_name
        obj.category_desc = category_desc
        obj.save()
        return redirect('customadminapp:categories')

    return render(request, "admin/categories.html")
@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def delete_category(request,id):


    user_obj=Category.objects.get(id=id)
    user_obj.delete()
    return redirect('customadminapp:categories')


@never_cache
def products(request):
        datas=Product.objects.all()
        categories=Category.objects.all()
        today_date = datetime.today().date()
        return render(request,"admin/products.html",{"datas":datas,"categories":categories,"today_date":today_date})
@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def add_products(request):

    if request.method == "POST":

        product_name = request.POST.get("product_name")
        description = request.POST.get("description")
        price = request.POST.get("price")
        images = request.FILES.getlist("images")  # Use getlist to get multiple images
        is_available = request.POST.get('is_available', False) == 'on'

        category_id = request.POST.get("category")
        category = Category.objects.get(pk=category_id)
        created_date = request.POST.get("created_date")
        updated_date = request.POST.get("updated_date")

        # Create the Product instance
        product = Product(
            product_name=product_name,
            description=description,
            price=price,
            is_available=is_available,
            category=category,
            created_date=created_date,
            updated_date=updated_date,
        )
        product.save()  # Save the product first

        # Add multiple images to the product
        for image in images:
            product_image = ProductImage(product=product, image=image)
            product_image.save()

        return redirect('customadminapp:products')
    return render(request, 'admin/products.html')

@login_required(login_url='admin_signin')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def update_product(request, id):
    obj = get_object_or_404(Product, id=id)

    if request.method == "POST":
        product_name = request.POST.get("product_name")
        description = request.POST.get("description")
        price = request.POST.get("price")
        quantity=request.POST.get("quantity")
        is_available = request.POST.get('is_available')
        if is_available == 'on':
            is_available = True
        else:
            is_available = False

        category_id = request.POST.get("category")
        selected_category = get_object_or_404(Category, id=category_id)
        created_date = request.POST.get("created_date")
        updated_date = request.POST.get("updated_date")

        # Update the product fields
        obj.product_name = product_name
        obj.description = description
        obj.price = price
        obj.quantity=quantity
        obj.is_available = is_available
        obj.category = selected_category
        obj.created_date = created_date
        obj.updated_date = updated_date
        obj.save()

        # Handle the product image
        new_image = request.FILES.get("image")
        if new_image:
            # Delete existing product images
            obj.images.all().delete()  # Assuming you have a related_name='images'

            # Create a new product image
            product_image = ProductImage(product=obj, image=new_image)
            product_image.save()

        return redirect('customadminapp:products')

    return render(request, "admin/products.html")

@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def delete_product(request,id):
    try:
        product = get_object_or_404(Product, id=id)
        product.is_available = False  # Set the product as not available
        product.save()
    except Product.DoesNotExist:
        pass

    return redirect('customadminapp:products')
def admin_signout(request):
    logout(request)
    return redirect('shop:home')

def manage_order(request):
        # orders=Order.objects.all()
        orders = Order.objects.all().order_by('-created_at')

        return render(request,"admin/manage_order.html",{"orders":orders})
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        # Redirect back to the orders page or a success page
        return redirect('customadminapp:manage_order')
def manage_coupon(request):

        coupons = Coupon.objects.all().order_by('-created_at')
        return render(request,"admin/manage_coupon.html",{"coupons":coupons})

@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def add_coupon(request):

    if request.method == "POST":

        coupon_code = request.POST.get("coupon_code")
        is_available = request.POST.get('is_available')
        if is_available == 'on':
            is_available = True
        else:
            is_available = False
        discount_price = request.POST.get("discount_price")
        minimum_amount = request.POST.get("minimum_amount")
        created_at = request.POST.get("created_at")
        updated_at = request.POST.get("updated_at")

        # Create the Product instance
        coupon = Coupon(
            coupon_code=coupon_code,
            is_available=is_available,
            discount_price=discount_price,
            minimum_amount=minimum_amount,
            created_at=created_at,
            updated_at=updated_at,
        )

        coupon.save()  # Save the product first


        return redirect('customadminapp:manage_coupon')
    return render(request, 'admin/manage_coupon.html')

@login_required(login_url='admin_signin')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def update_coupon(request, id):
    obj = get_object_or_404(Coupon, id=id)
    if request.method == "POST":
        coupon_code= request.POST.get("coupon_code")
        discount_price = request.POST.get("discount_price")
        minimum_amount = request.POST.get("minimum_amount")
        is_available = request.POST.get('is_available')
        if is_available == 'on':
            is_available = True
        else:
            is_available = False
        created_at = request.POST.get("created_at")
        updated_at = request.POST.get("updated_at")

        # Update the product fields
        obj.coupon_code = coupon_code
        obj.discount_price =discount_price
        obj.minimum_amount = minimum_amount
        obj.is_available = is_available
        obj.created_at = created_at
        obj.updated_at = updated_at
        obj.save()
        return redirect('customadminapp:manage_coupon')

    return render(request, "admin/manage_coupon.html")

@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def blockcoupon(request,id):

    obj=Coupon.objects.get(id=id)
    obj.is_available=False
    obj.save()
    return redirect('customadminapp:manage_coupon')

@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def unblockcoupon(request,id):


    obj=Coupon.objects.get(id=id)
    obj.is_available=True
    obj.save()
    return redirect('customadminapp:manage_coupon')

@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def manage_offer(request):

        offers = CategoryOffer.objects.all().order_by('-created_at')
        categories=Category.objects.all()


        return render(request,"admin/manage_offer.html",{"offers":offers,'categories':categories})

def manage_product_offer(request):
     product_offers = ProductOffer.objects.all().order_by('-created_at')
     products=Product.objects.all()
     return render(request,"admin/manage_product_offer.html",{"product_offers":product_offers,'products':products})
@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def add_product_offer(request):

    if request.method == "POST":

        title = request.POST.get("title")
        is_available = request.POST.get('is_available', False) == 'on'
        description = request.POST.get("description")
        discount_value = request.POST.get("discount_value")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        created_at = request.POST.get("created_at")
        updated_at = request.POST.get("updated_at")
        product_id = request.POST.get("product")
        product = Product.objects.get(pk=product_id)
        # Create the Product instance
        productOffer = ProductOffer(
            title=title,
            is_available=is_available,
            description=description,
            discount_value=discount_value,
            created_at=created_at,
            updated_at=updated_at,
            start_date=start_date,
            end_date=end_date,
            product=product
        )
        productOffer.save()  # Save the product first
        return redirect('customadminapp:manage_product_offer')
    return render(request, 'admin/manage_product_offer.html')

@login_required(login_url='admin_signin')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def add_offer(request):

    if request.method == "POST":

        title = request.POST.get("title")
        is_available = request.POST.get('is_available', False) == 'on'
        description = request.POST.get("description")
        discount_value = request.POST.get("discount_value")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        created_at = request.POST.get("created_at")
        updated_at = request.POST.get("updated_at")
        category_id = request.POST.get("category")
        category = Category.objects.get(pk=category_id)
        # Create the Product instance
        categoryoffer = CategoryOffer(
            title=title,
            is_available=is_available,
            description=description,
            discount_value=discount_value,
            created_at=created_at,
            updated_at=updated_at,
            start_date=start_date,
            end_date=end_date,
            category=category
        )
        categoryoffer.save()  # Save the product first
        return redirect('customadminapp:manage_offer')
    return render(request, 'admin/manage_offer.html')
@login_required(login_url='admin_signin')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def update_offer(request, id):
    obj = get_object_or_404(CategoryOffer, id=id)
    if request.method == "POST":
        title= request.POST.get("title")
        description = request.POST.get("description")
        discount_value = request.POST.get("discount_value")
        is_available = request.POST.get('is_available', False) == 'on'
        created_at = request.POST.get("created_at")
        updated_at = request.POST.get("updated_at")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        category_id = request.POST.get("category")
        selected_category = get_object_or_404(Category, id=category_id)
        # Update the product fields
        obj.title= title
        obj.description =description
        obj.discount_value = discount_value
        obj.is_available = is_available
        obj.created_at = created_at
        obj.updated_at = updated_at
        obj.start_date = start_date
        obj.end_date = end_date
        obj.category=selected_category
        obj.save()
        return redirect('customadminapp:manage_offer')
    return render(request, "admin/manage_offer.html")
@login_required(login_url='admin_signin')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def update_product_offer(request, id):
    obj = get_object_or_404(ProductOffer, id=id)
    if request.method == "POST":
        title= request.POST.get("title")
        description = request.POST.get("description")
        discount_value = request.POST.get("discount_value")
        is_available = request.POST.get('is_available', False) == 'on'
        created_at = request.POST.get("created_at")
        updated_at = request.POST.get("updated_at")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        product_id = request.POST.get("product")
        selected_product = get_object_or_404(Product, id=product_id)
        # Update the product fields
        obj.title= title
        obj.description =description
        obj.discount_value = discount_value
        obj.is_available = is_available
        obj.created_at = created_at
        obj.updated_at = updated_at
        obj.start_date = start_date
        obj.end_date = end_date
        obj.product=selected_product
        obj.save()
        return redirect('customadminapp:manage_product_offer')
    return render(request, "admin/manage_product_offer.html")
def sales_report(request):
    if not request.user.is_superuser:
        return redirect('customadminapp:admin_signin')

    context = {}

    if request.method == 'POST':
        start_date = request.POST.get('start-date')
        end_date = request.POST.get('end-date')
        report_type = request.POST.get('report-type')

        if start_date == '' or end_date == '':
            messages.error(request, 'Please enter the date first')
            return redirect('customadminapp:sales_report')

        try:
            start_date_obj = timezone.datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = timezone.datetime.strptime(end_date, '%Y-%m-%d')
            start_date_obj = timezone.make_aware(start_date_obj)
            end_date_obj = timezone.make_aware(end_date_obj)
        except ValueError:
            messages.error(request, 'Invalid date format')
            return redirect('customadminapp:sales_report')

        order_items = None
        category_sales = None
        unique_order_ids = set()
        final_total =0
        if report_type == 'all':
            if start_date_obj != end_date_obj:
                order_items = (
    OrderProduct.objects
    .filter(
        order__created_at__range=[start_date_obj, end_date_obj],
        order__status__in=['New', 'Accepted', 'Shipped']
    )
    .select_related('order', 'product')
    .distinct('order__id')
)
            else:
                order_items = (
                    OrderProduct.objects
                    .filter(order__created_at__date=start_date_obj.date(),
                          order__status__in=['New', 'Accepted', 'Shipped']
                            )
                    .select_related('order', 'product')
                    .distinct('order__id')
                )
            final_total = sum(entry.order.total_with_tax for entry in order_items)

        elif report_type == 'product':

            if start_date_obj != end_date_obj:
                product_sales = (
                OrderProduct.objects
                .filter(order__created_at__range=[start_date_obj, end_date_obj],
                         order__status__in=['New', 'Accepted', 'Shipped']
                        )
                .values('product__product_name')
                .annotate(
                    total_sales=Sum('order__total_with_tax'),
                    total_quantity=Sum('quantity'),
                )
                .order_by('-total_sales')
            )

            else:
                order_items = (
                    OrderProduct.objects
                    .filter(order__created_at__date=start_date_obj.date(),
                          order__status__in=['New', 'Accepted', 'Shipped']
                            )
                    .select_related('order', 'product')
                    .distinct('order__id')
                )
                final_total = sum(entry.order.total_with_tax for entry in order_items)
                order_items=None
                product_sales = (
                OrderProduct.objects
                .filter(order__created_at__date=start_date_obj.date(),
                         order__status__in=['New', 'Accepted', 'Shipped']
                        )
                .values('product__product_name')
                .annotate(
                    total_sales=Sum('order__total_with_tax'),
                    total_quantity=Sum('quantity'),
                )
                .order_by('-total_sales')
                )
            for entry in product_sales:
                product_orders = OrderProduct.objects.filter(
                    product__product_name=entry['product__product_name'],
                    order__created_at__range=[start_date_obj, end_date_obj],
                     order__status__in=['New', 'Accepted', 'Shipped']
                ).select_related('order', 'product').order_by('-order__created_at')

                for product_entry in product_orders:
                    if product_entry.order.id not in unique_order_ids:
                        final_total += product_entry.order.total_with_tax
                        unique_order_ids.add(product_entry.order.id)

            context.update(product_sales=product_sales, final_total=final_total)

        elif report_type == 'category':

            # Group by category and annotate with total sales and total products
            if start_date_obj != end_date_obj:

                category_sales = (
                OrderProduct.objects
                .filter(order__created_at__range=[start_date_obj, end_date_obj],
                         order__status__in=['New', 'Accepted', 'Shipped']
                        )
                .values('product__category__category_name')
                .annotate(
                    total_sales=Sum('order__total_with_tax'),
                    total_products=Count('id'),
                )
                .order_by('-total_sales')
            )
            else:
                order_items = (
                    OrderProduct.objects
                    .filter(order__created_at__date=start_date_obj.date(),
                          order__status__in=['New', 'Accepted', 'Shipped']
                            )
                    .select_related('order', 'product')
                    .distinct('order__id')
                )
                final_total = sum(entry.order.total_with_tax for entry in order_items)
                order_items=None
                category_sales = (
                OrderProduct.objects
                .filter(order__created_at__date=start_date_obj.date(),
                         order__status__in=['New', 'Accepted', 'Shipped']
                        )
                .values('product__category__category_name')
                .annotate(
                    total_sales=Sum('order__total_with_tax'),
                    total_products=Count('id'),
                )
                .order_by('-total_sales')
            )
            unique_order_ids_category = set()  # To keep track of unique order IDs for category


            for entry in category_sales:
                category_orders = OrderProduct.objects.filter(
                    product__category__category_name=entry['product__category__category_name'],
                    order__created_at__range=[start_date_obj, end_date_obj],
                     order__status__in=['New', 'Accepted', 'Shipped']
                ).select_related('order', 'product').order_by('-order__created_at')

                for category_entry in category_orders:
                    if category_entry.order.id not in unique_order_ids_category:
                        final_total += category_entry.order.total_with_tax
                        unique_order_ids_category.add(category_entry.order.id)

            context.update(category_sales=category_sales, final_total=final_total)


        if order_items:
            context.update(sales=order_items,final_total=final_total)

        # Update context with start date and end date
        context.update(s_date=start_date, e_date=end_date,final_total=final_total)

    return render(request, 'admin/sales_report.html', context)
def download_invoice_pdf(request):
    try:
        order_items = OrderProduct.objects.select_related('order', 'product').exclude(order__status__iexact='Cancelled').distinct('order__id')
        category_sales = None
        unique_order_ids = set()
        product_sales = (
            OrderProduct.objects
            .exclude(order__status__iexact='Cancelled')
            .values('product__product_name')
            .annotate(
                total_sales=Sum('order__total_with_tax'),
                total_quantity=Sum('quantity'),
            )
            .order_by('-total_sales')
        )

        final_total = 0

        for entry in product_sales:
            product_orders = OrderProduct.objects.filter(
                product__product_name=entry['product__product_name']
            ).select_related('order', 'product').order_by('-order__created_at')

            for product_entry in product_orders:
                if product_entry.order.id not in unique_order_ids:
                    final_total += product_entry.order.total_with_tax
                    unique_order_ids.add(product_entry.order.id)

        category_sales = (
            OrderProduct.objects
            .exclude(order__status__iexact='Cancelled')
            .values('product__category__category_name')
            .annotate(
                total_sales=Sum('order__total_with_tax'),
                total_products=Count('id'),
            )
            .order_by('-total_sales')
        )
        final_total = sum(entry.order.total_with_tax for entry in order_items if entry.order.status.lower() != 'cancelled')


        unique_order_ids_category = set()

        for entry in category_sales:
            category_orders = OrderProduct.objects.filter(
                product__category__category_name=entry['product__category__category_name']
            ).select_related('order', 'product').order_by('-order__created_at')

            for category_entry in category_orders:
                if category_entry.order.id not in unique_order_ids_category:
                    # final_total += category_entry.order.order_total
                    unique_order_ids_category.add(category_entry.order.id)

        template_path = 'admin/invoice_pdf.html'  # Provide the correct path to your HTML template
        context = {'final_total': final_total, 'order_items': order_items, 'category_sales': category_sales, 'product_sales': product_sales}

        # Render the template
        template = get_template(template_path)
        html = template.render(context)

        # Create a PDF file
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_string = str(uuid.uuid4().hex[:8])
        file_name = f'invoice_{timestamp}_{random_string}.pdf'

        # Set the response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')

        return response
    except Exception as e:
        return HttpResponse(f'Error: {e}')

def download_invoice_excel(request):
    try:
        order_items = None
        category_sales = None
        unique_order_ids = set()
        order_items = OrderProduct.objects.select_related('order', 'product').exclude(order__status__iexact='Cancelled').distinct('order__id')


        product_sales = (
            OrderProduct.objects
            .exclude(order__status__iexact='Cancelled')
            .values('product__product_name')
            .annotate(
                total_sales=Sum('order__total_with_tax'),
                total_quantity=Sum('quantity'),
            )
            .order_by('-total_sales')
        )

        for entry in product_sales:
            product_orders = OrderProduct.objects.filter(
                product__product_name=entry['product__product_name']
            ).select_related('order', 'product').order_by('-order__created_at')

            for product_entry in product_orders:
                if product_entry.order.id not in unique_order_ids:
                    # final_total += product_entry.order.order_total
                    unique_order_ids.add(product_entry.order.id)

        category_sales = (
            OrderProduct.objects
            .exclude(order__status__iexact='Cancelled')
            .values('product__category__category_name')
            .annotate(
                total_sales=Sum('order__total_with_tax'),
                total_products=Count('id'),
            )
            .order_by('-total_sales')
        )
        final_total = sum(entry.order.total_with_tax for entry in order_items if entry.order.status.lower() != 'cancelled')
        # Create a DataFrame for product sales
        product_sales_df = pd.DataFrame(list(product_sales))
        final_total_row_product = pd.DataFrame({'Product': 'Final Total', 'Total Sales': final_total}, index=[0])

        # Concatenate the final total row to the product_sales_df
        product_sales_df = pd.concat([product_sales_df, final_total_row_product])
 # Create a DataFrame for category sales
        category_sales_df = pd.DataFrame(list(category_sales))
        # Create a row for the final total in category_sales_df
        final_total_row_category = pd.DataFrame({'Category': 'Final Total', 'Total Sales': final_total}, index=[0])

        # Concatenate the final total row to the category_sales_df
        category_sales_df = pd.concat([category_sales_df, final_total_row_category])


        order_summary_df = pd.DataFrame({
    'Order ID': [order_item.order.order_number for order_item in order_items],
    'Customer Name': [order_item.user for order_item in order_items],
    'Product': [', '.join([order_product.product.product_name for order_product in order_item.order.orderproduct_set.all()]) for order_item in order_items],
    'Order Date': [order_item.created_at.astimezone(timezone.utc).replace(tzinfo=None) for order_item in order_items],
    'Price': [order_item.order.total_with_tax for order_item in order_items],
           })
     # Create a row for the final total in order_summary_df
        final_total_row_order_summary = pd.DataFrame({'Order ID': 'Final Total', 'Price': final_total}, index=[0])

        # Concatenate the final total row to the order_summary_df
        order_summary_df = pd.concat([order_summary_df, final_total_row_order_summary])


        # Create a buffer to hold the Excel file
        output = io.BytesIO()

        # Create a Pandas Excel writer using XlsxWriter as the engine
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write each DataFrame to a different worksheet
            product_sales_df.to_excel(writer, sheet_name='Product Sales', index=False)
            category_sales_df.to_excel(writer, sheet_name='Category Sales', index=False)
            order_summary_df.to_excel(writer, sheet_name='Order Summary', index=False)

        # Set the buffer's position to the start
        output.seek(0)

        # Create a response with the correct MIME type
        response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=sales_report.xlsx'

        return response

    except Exception as e:
        return HttpResponse(f'Error: {e}')





