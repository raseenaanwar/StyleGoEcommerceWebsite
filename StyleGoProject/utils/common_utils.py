# utils/common_utils.py

from shop.models import ProductOffer, CategoryOffer

def calculate_offered_price(product):
    try:
        product_offer = ProductOffer.objects.get(product=product)
        category_offer = CategoryOffer.objects.get(category=product.category)

        if category_offer.discount_value > product_offer.discount_value:
            discount_amount = category_offer.discount_value
        else:
            discount_amount = product_offer.discount_value

        return product.price - discount_amount

    except ProductOffer.DoesNotExist or CategoryOffer.DoesNotExist:
        return product.price
