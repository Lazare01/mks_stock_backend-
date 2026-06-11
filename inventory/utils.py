from inventory.models import Category,Product

def generate_sku(category):
    prefix = Category.sku_prefix(category)

    last_product = (
        Product.objects.filter(sku__startswith=prefix).order_by("-sku").first()
    )

    if not last_product:
        return f"{prefix}-000001"

    last_number = int(last_product.sku.split("-")[1])

    return f"{prefix}-{last_number + 1:06d}"


