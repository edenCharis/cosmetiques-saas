from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from core.tenancy import get_current_tenant


class TenantAwareManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant is None:
            # ✅ Return empty queryset instead of everything
            return qs.none()
        return qs.filter(tenant=tenant)


# ---------------------------
# Tenant
# ---------------------------
class Tenant(models.Model):
    name = models.CharField(max_length=200, unique=True)
    domain = models.CharField(max_length=255, unique=True)  # e.g. tenant.example.com or custom domain
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


# ---------------------------
# Custom User Model (extends Django's AbstractUser)
# ---------------------------
class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.
    This replaces the default Django User model.
    """
    tenant = models.ForeignKey(
        Tenant, 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='users'
    )

    def __str__(self):
        return self.username


# ---------------------------
# User <-> Tenant association
# ---------------------------

# ---------------------------
# Produit Cosmétique
# ---------------------------
class Category(models.Model):
    tenant = models.ForeignKey(Tenant, null=True, blank=True, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)

    objects = TenantAwareManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ('tenant', 'name')

    def __str__(self):
        return self.name


# models.py
class Product(models.Model):
    tenant = models.ForeignKey(Tenant, null=True, blank=True, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', null=True, blank=True)  # ✅ NOUVEAU
    created_at = models.DateTimeField(default=timezone.now)

    objects = TenantAwareManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ('tenant', 'name')

    def __str__(self):
        return f"{self.name} ({self.category.name})"


# ---------------------------
# Client
# ---------------------------
class Client(models.Model):
    tenant = models.ForeignKey(Tenant, null=True, blank=True, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    area = models.CharField(max_length=100)  # quartier / ville
    created_at = models.DateTimeField(default=timezone.now)

    objects = TenantAwareManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ('tenant', 'phone')

    def __str__(self):
        return f"{self.name} - {self.phone}"


# ---------------------------
# Commande
# ---------------------------
class Order(models.Model):
    tenant = models.ForeignKey(Tenant, null=True, blank=True, on_delete=models.CASCADE, related_name='orders')

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

    objects = TenantAwareManager()
    all_objects = models.Manager()

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