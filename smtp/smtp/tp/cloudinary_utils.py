from django.conf import settings

try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
except Exception:
    cloudinary = None


def upload_image(file, folder=None):
    """Upload a file (file-like or path) to Cloudinary if installed.
    Returns secure_url on success.
    """
    if cloudinary is None:
        raise RuntimeError('cloudinary package not installed. pip install cloudinary')

    cloudinary.config(
        cloud_name=getattr(settings, 'CLOUDINARY_CLOUD_NAME', ''),
        api_key=getattr(settings, 'CLOUDINARY_API_KEY', ''),
        api_secret=getattr(settings, 'CLOUDINARY_API_SECRET', ''),
        secure=True,
    )

    options = {}
    if folder:
        options['folder'] = folder
    res = cloudinary.uploader.upload(file, **options)
    return res.get('secure_url')
