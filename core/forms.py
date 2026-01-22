from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from core.models import Tenant, User
from .models import Product, Client, Order, Category, OrderItem

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    """
    Form for registering new users with email and password confirmation.
    Also creates a tenant for each new user.
    """
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'placeholder': 'votre@email.com',
            'autocomplete': 'email'
        })
    )
    
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Créez un mot de passe sécurisé',
            'autocomplete': 'new-password'
        })
    )
    
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Saisissez à nouveau votre mot de passe',
            'autocomplete': 'new-password'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Choisissez un nom d\'utilisateur unique',
                'autocomplete': 'username'
            })
        }

    def clean_email(self):
        """Ensure email is unique"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return email

    def clean_password2(self):
        """Verify that passwords match"""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Les mots de passe ne correspondent pas.")
            
            # Password strength validation
            if len(password1) < 8:
                raise forms.ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
            
            if not any(char.isdigit() for char in password1):
                raise forms.ValidationError("Le mot de passe doit contenir au moins un chiffre.")
            
            if not any(char.isalpha() for char in password1):
                raise forms.ValidationError("Le mot de passe doit contenir au moins une lettre.")
        
        return password2

    def save(self, commit=True):
        """
        Save the user and create associated tenant.
        
        This method:
        1. Creates a tenant with the username as the tenant name
        2. Creates the user with the hashed password AND links to tenant
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        
        if commit:
            with transaction.atomic():
                # Create or get tenant
                tenant_name = self.cleaned_data['username']
                tenant, created = Tenant.objects.get_or_create(
                    name=tenant_name,
                    defaults={'domain': f"{tenant_name}.example.com"}  # Better default domain
                )
                
                # Link tenant to user BEFORE saving
                user.tenant = tenant
                
                # Save user with tenant already set
                user.save()
                
                print(f"✅ User created: {user.username}")
                print(f"✅ Tenant {'created' if created else 'found'}: {tenant.name}")
                print(f"✅ User.tenant = {user.tenant}")
        
        return user


class TenantAwareAuthenticationForm(AuthenticationForm):
    """
    If you detect tenant by host, ensure the authenticating user belongs to that tenant.
    """
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)

        request = getattr(self, "request", None)
        if not request:
            # Request not available (form not instantiated with request) — nothing to check.
            return

        try:
            host = request.get_host().split(':')[0].lower()
        except Exception:
            # Could not determine host — skip tenant check or deny based on your policy
            return

        host_tenant = Tenant.objects.filter(domain__iexact=host).first()
        if host_tenant:
            user_tenant = getattr(user, "tenant", None)
            if not user_tenant or user_tenant.id != host_tenant.id:
                raise forms.ValidationError(
                    "Ce compte n'appartient pas à ce tenant.",
                    code="invalid_tenant"
                )

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'stock', 'image']
        labels = {
            'name': 'Nom du produit',
            'category': 'Catégorie',
            'price': 'Prix (FCFA)',
            'stock': 'Stock disponible',
            'image': "Image du produit",
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ex: Crème hydratante'}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'min': '0'}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        # ✅ Accepte le tenant en paramètre
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

        # ✅ Filtre les catégories par tenant
        if tenant:
            self.fields['category'].queryset = Category.all_objects.filter(tenant=tenant)
        else:
            # Si pas de tenant, liste vide
            self.fields['category'].queryset = Category.objects.none()

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            return image

        # Basic validation: ensure file is an image and not too large (max 5MB)
        content_type = getattr(image, 'content_type', '')
        if not content_type.startswith('image/'):
            raise forms.ValidationError("Le fichier doit être une image.")

        max_size = 5 * 1024 * 1024  # 5 MB
        if image.size > max_size:
            raise forms.ValidationError("L'image est trop volumineuse (max 5MB).")

        return image


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'phone', 'area']
        labels = {
            'name': 'Nom complet',
            'phone': 'Téléphone',
            'area': 'Quartier',
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        labels = {
            'name': 'Nom de la catégorie',
        }

class UserLoginForm(AuthenticationForm):

    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={'autofocus': True, 'autocomplete': 'username'})
    )
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'})
    )

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['client', 'status', 'delivery_fee', 'total_amount', 'delivery_mode']
        labels = {
            'client': 'Client',
            'delivery_fee' : ' Frais de livraison',
            'status': 'status',
            'total_amount': 'Montant total',
            'delivery_mode': 'Mode de livraison '
        }
        widgets = {
            'delivery_mode': forms.Select(choices=Order.DELIVERY_CHOICES),
            'status': forms.Select(choices=Order.STATUS_CHOICES),
        }

        def __init__(self, *args, **kwargs):
            tenant = kwargs.pop('tenant', None)
            super().__init__(*args, **kwargs)

            # Filtrer les clients par tenant
            if tenant:
                self.fields['client'].queryset = Client.all_objects.filter(tenant=tenant)
            else:
                self.fields['client'].queryset = Client.objects.none()




class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem # Utilise le modèle intermédiaire
        fields = ['product', 'quantity', 'price']
        labels = {
            'product': 'Produit',
            'quantity': 'Quantité',
            'price': 'Prix unitaire',
        }  

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

        # Filtrer les produits par tenant
        if tenant:
            self.fields['product'].queryset = Product.all_objects.filter(tenant=tenant)
        else:
            self.fields['product'].queryset = Product.objects.none() 