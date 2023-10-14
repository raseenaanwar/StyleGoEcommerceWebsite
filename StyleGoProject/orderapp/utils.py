from django.shortcuts import get_object_or_404
from shop.models import ProductVariant
def get_product_variant_for_order(order_id, product_id, selected_color, selected_size):
    try:
        product_variant = get_object_or_404(
            ProductVariant,
            product_id=product_id,  # Use the correct field name for product_id
            colors=selected_color,  # This assumes 'selected_color' is a Color instance
            sizes=selected_size,    # This assumes 'selected_size' is a Size instance
        )
        return product_variant
    except ProductVariant.DoesNotExist:
        return None
