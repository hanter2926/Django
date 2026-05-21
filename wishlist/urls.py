from django.urls import path
from .views import add_to_wishlist, wishlist_view, remove_wishlist

urlpatterns = [

    path('', wishlist_view, name='wishlist'),

    path('add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),

    path('remove/<int:wishlist_id>/', remove_wishlist, name='remove_wishlist'),
]