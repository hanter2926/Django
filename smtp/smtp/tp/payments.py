try:
    import razorpay
except Exception:
    razorpay = None

from django.conf import settings


def get_razorpay_client():
    if razorpay is None:
        raise RuntimeError('razorpay package not installed. pip install razorpay')
    key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
    if not key_id or not key_secret:
        raise RuntimeError('Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in settings')
    return razorpay.Client(auth=(key_id, key_secret))


def create_order(amount_in_rupees, currency='INR', receipt=None, notes=None):
    client = get_razorpay_client()
    # Razorpay expects amount in paise (subunits)
    amount = int(float(amount_in_rupees) * 100)
    data = {
        'amount': amount,
        'currency': currency,
    }
    if receipt:
        data['receipt'] = receipt
    if notes:
        data['notes'] = notes
    return client.order.create(data)


def verify_payment_signature(order_id, payment_id, signature):
    client = get_razorpay_client()
    params_dict = {
        'razorpay_order_id': order_id,
        'razorpay_payment_id': payment_id,
        'razorpay_signature': signature
    }
    return client.utility.verify_payment_signature(params_dict)


def verify_webhook_signature(body, signature, secret):
    if razorpay is None:
        raise RuntimeError('razorpay package not installed. pip install razorpay')
    client = get_razorpay_client()
    return client.utility.verify_webhook_signature(body, signature, secret)
