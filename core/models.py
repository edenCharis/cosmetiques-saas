from django.db import models
from django.utils import timezone

# ---------------------------
# Produit Cosmétique
# ---------------------------
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('creme', 'Crème'),
        ('parfum', 'Parfum'),
        ('maquillage', 'Maquillage'),
        ('soin', 'Soin'),
        ('autre', 'Autre'),
    ]

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='autre')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.category})"


# ---------------------------
# Client
# ---------------------------
class Client(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    area = models.CharField(max_length=100)  # quartier / ville
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} - {self.phone}"


# ---------------------------
# Commande
# ---------------------------
class Order(models.Model):
    DELIVERY_CHOICES = [
        ('retrait', 'Retrait en magasin'),
        ('livraison', 'Livraison à domicile'),
    ]

    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('delivered', 'Livré'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    delivery_mode = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='retrait')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Commande #{self.id} - {self.client.name}"


# ---------------------------
# Items de Commande
# ---------------------------
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # prix unitaire au moment de la commande

    def __str__(self):
        return f"{self.quantity} x {self.product.name} pour {self.order.client.name}"
