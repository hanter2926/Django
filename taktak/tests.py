from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from .catalog import discover_catalog
from .models import Announcement, Category, ContactMessage, GalleryImage, Order, Product, TeamMember


class ModelTests(TestCase):
    def test_category_and_product_creation(self):
        category = Category.objects.create(name='Accessories', slug='accessories')
        product = Product.objects.create(
            name='Leather Bag',
            slug='leather-bag',
            description='A premium leather bag',
            price=89.99,
            category=category,
            stock=10,
        )

        self.assertEqual(category.name, 'Accessories')
        self.assertEqual(product.category, category)
        self.assertGreaterEqual(product.price, 0)

    def test_content_models_can_be_created(self):
        Announcement.objects.create(message='Spring sale now live!', is_active=True)
        ContactMessage.objects.create(
            name='Dana',
            email='dana@example.com',
            subject='Support',
            message='I need help with my order.'
        )
        TeamMember.objects.create(
            employee_name='Asha',
            role='Designer',
            description='Leads product design.'
        )
        GalleryImage.objects.create(title='Studio', caption='New collection launch')

        self.assertEqual(Announcement.objects.count(), 1)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertEqual(TeamMember.objects.count(), 1)
        self.assertEqual(GalleryImage.objects.count(), 1)

    def test_products_page_renders_dynamic_catalog(self):
        response = self.client.get(reverse('product_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Our Products')

    def test_sell_product_form_creates_product(self):
        category = Category.objects.create(name='Electronics', slug='electronics')

        response = self.client.post(reverse('sell_product'), {
            'name': 'Smartphone',
            'description': 'Used smartphone in good condition',
            'price': '150.00',
            'stock': '1',
            'category': category.id,
            'is_featured': False,
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(name='Smartphone').exists())

    def test_search_returns_matching_products_from_database(self):
        category = Category.objects.create(name='Accessories', slug='accessories')
        Product.objects.create(
            name='Leather Bag',
            slug='leather-bag',
            description='A premium leather bag',
            price=89.99,
            category=category,
            stock=10,
        )

        response = self.client.get(reverse('product_list'), {'q': 'bag'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Leather Bag')
        self.assertContains(response, 'Search results for "bag"')

    def test_search_shows_no_results_message_when_nothing_matches(self):
        category = Category.objects.create(name='Accessories', slug='accessories')
        Product.objects.create(
            name='Leather Bag',
            slug='leather-bag',
            description='A premium leather bag',
            price=89.99,
            category=category,
            stock=10,
        )

        response = self.client.get(reverse('product_list'), {'q': 'headphones'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No results found')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_registration_creates_user_and_logs_in_after_otp_verification(self):
        User = get_user_model()

        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'phone': '9876543210',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertIn('signup_otp', self.client.session)

        otp = self.client.session['signup_otp']
        verify_response = self.client.post(reverse('verify_otp'), {'otp': otp})

        self.assertEqual(verify_response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertTrue(self.client.session.get('_auth_user_id'))

    def test_checkout_creates_order_from_cart(self):
        category = Category.objects.create(name='Accessories', slug='accessories')
        product = Product.objects.create(
            name='Leather Bag',
            slug='leather-bag',
            description='A premium leather bag',
            price=89.99,
            category=category,
            stock=10,
        )
        session = self.client.session
        session['cart'] = [{
            'category_slug': category.slug,
            'product_slug': product.slug,
            'name': product.name,
            'price': float(product.price),
            'image_url': '',
            'quantity': 1,
        }]
        session.save()

        response = self.client.post(reverse('checkout'), {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'address': '123 Test Street',
            'city': 'Test City',
            'payment_method': 'cod',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Order.objects.exists())

    def test_logged_in_buyer_can_submit_review(self):
        user = get_user_model().objects.create_user(username='buyer', email='buyer@example.com', password='StrongPass123')
        category = Category.objects.create(name='Accessories', slug='accessories')
        product = Product.objects.create(
            name='Leather Bag',
            slug='leather-bag',
            description='A premium leather bag',
            price=89.99,
            category=category,
            stock=10,
        )
        order = Order.objects.create(
            customer_name='Buyer',
            email='buyer@example.com',
            phone='1234567890',
            address='123 Test',
            city='Test City',
            total=89.99,
            items='Leather Bag x1',
            user=user,
            status='Delivered',
            payment_status='Paid',
        )
        order.items_set.create(product=product, product_name=product.name, product_slug=product.slug, quantity=1, price=product.price)

        self.client.force_login(user)
        response = self.client.post(reverse('submit_review', args=[product.slug]), {
            'rating': '5',
            'comment': 'Excellent product.',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(product.reviews.filter(user=user).exists())

    def test_discover_catalog_reads_folder_structure(self):
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            category_dir = root / 'Category' / 'Electronics'
            product_dir = category_dir / 'Smartphone'
            product_dir.mkdir(parents=True)
            (product_dir / 'front.jpg').write_bytes(b'fake image')

            catalog = discover_catalog(root)

            self.assertEqual(len(catalog), 1)
            self.assertEqual(catalog[0]['name'], 'Electronics')
            self.assertEqual(len(catalog[0]['products']), 1)
            self.assertEqual(catalog[0]['products'][0]['name'], 'Smartphone')
            self.assertEqual(len(catalog[0]['products'][0]['images']), 1)
