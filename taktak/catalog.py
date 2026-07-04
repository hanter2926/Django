from pathlib import Path
from typing import Dict, List

from django.templatetags.static import static
from django.utils.text import slugify


def discover_catalog(root: Path | str | None = None) -> List[Dict]:
    if root is None:
        base_root = Path(__file__).resolve().parent.parent / 'static' / 'taktak' / 'images' / 'Category'
    else:
        base_root = Path(root)

    if base_root.name.lower() == 'category':
        base_root = base_root
    elif base_root.name.lower() == 'images':
        base_root = base_root / 'Category'
    elif (base_root / 'Category').exists():
        base_root = base_root / 'Category'

    if not base_root.exists():
        return []

    categories = []
    for category_dir in sorted(base_root.iterdir()):
        if not category_dir.is_dir():
            continue

        products = []
        for product_dir in sorted(category_dir.iterdir()):
            if not product_dir.is_dir():
                continue

            image_files = []
            for image_path in sorted(product_dir.rglob('*')):
                if image_path.is_file() and image_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'}:
                    image_files.append(image_path)

            image_urls = []
            for image_path in image_files:
                relative_path = Path('taktak/images/Category') / image_path.relative_to(base_root)
                image_urls.append(static(relative_path.as_posix()))

            products.append({
                'name': product_dir.name,
                'slug': slugify(product_dir.name),
                'description': f'{product_dir.name} is a featured item from the {category_dir.name} collection.',
                'price': round(29.99 + (len(products) * 8.5), 2),
                'images': image_urls,
                'folder': str(product_dir),
            })

        category_card_image = None
        for image_path in sorted(category_dir.rglob('*')):
            if image_path.is_file() and image_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg', '.jfif', '.avif'}:
                relative_path = Path('taktak/images/Category') / image_path.relative_to(base_root)
                category_card_image = static(relative_path.as_posix())
                break

        if not category_card_image and products:
            category_card_image = products[0]['images'][0] if products[0]['images'] else None

        categories.append({
            'name': category_dir.name,
            'slug': slugify(category_dir.name),
            'products': products,
            'folder': str(category_dir),
            'card_image': category_card_image,
        })

    return categories
