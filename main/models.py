import uuid
from django.db import models
from django.core.validators import MinValueValidator
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('sepatu', 'Sepatu'),
        ('bola', 'Bola'),
        ('baju olahraga', 'Baju olahraga'),
        ('kaos kaki', 'Kaos kaki'),
        ('celana olahraga', 'Celana Olahraga'),
        ('raket', 'Raket'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    price = models.IntegerField(default=0, null=False, validators=[MinValueValidator(0)])
    description = models.TextField()
    thumbnail = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='sepatu')
    is_featured = models.BooleanField(default=False)
    
    def __str__(self):
        return self.id