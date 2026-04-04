from django.db import models

class SearchResult(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField()
    description = models.TextField()
    # Image field (Pillow library iske liye zaroori hai)
    image = models.ImageField(upload_to='results_pics/', null=True, blank=True)

    def __str__(self):
        return self.title
