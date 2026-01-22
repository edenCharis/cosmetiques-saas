from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from .models import Product, Client, Order, Category, OrderItem
from .forms import CategoryForm, ProductForm, UserRegistrationForm, ClientForm, OrderForm, OrderItemForm
from django.db import transaction
from decimal import Decimal
from django.db.models import Sum
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json


@login_required
def dashboard(request):
    """Tableau de bord principal - filtré automatiquement par tenant"""
    
    # Calcul du chiffre d'affaires total (somme de tous les montants des commandes)
    revenue_data = Order.objects.aggregate(
        total_revenue=Sum('total_amount')
    )
    total_revenue = revenue_data['total_revenue'] or Decimal('0')
    
    # Calcul du nombre de ventes (commandes livrées)
    total_sales = Order.objects.filter(status='delivered').count()
    
    context = {
        'total_products': Product.objects.count(),
        'total_clients': Client.objects.count(),
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'pending_orders': Order.objects.filter(status='pending').count(),
    }
    return render(request, 'dashboard.html', context)


@login_required
def category_list(request):
    """Liste des catégories - FILTRÉES AUTOMATIQUEMENT par tenant"""
    # Le TenantAwareManager filtre automatiquement
    categories = Category.objects.all().order_by('-created_at')
    return render(request, 'category/category_list.html', {'categories': categories})


@login_required
def category_create(request):
    """Créer une nouvelle catégorie - ASSOCIÉE AUTOMATIQUEMENT au tenant"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            
            # ✅ Récupérer le tenant de l'utilisateur
            try:
                tenant = request.user.tenant
                category.tenant = tenant
                category.save()
                messages.success(request, 'Catégorie ajoutée avec succès !')
                return redirect('category_list')
            except Exception as e:
                messages.error(request, f"Erreur: {e}")
    else:
        form = CategoryForm()
    
    return render(request, 'category/category_form.html', {'form': form})


@login_required
def category_delete(request, pk):
    """Supprimer une catégorie - VÉRIFICATION AUTOMATIQUE du tenant"""
    # Le TenantAwareManager s'assure que l'utilisateur ne peut accéder
    # qu'aux catégories de son propre tenant
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Catégorie supprimée avec succès !')
        return redirect('category_list')
    
    return render(request, 'category/category_confirm_delete.html', {'category': category})


@login_required
def product_list(request):
    """Liste des produits - FILTRÉS AUTOMATIQUEMENT par tenant"""
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'products/product_list.html', {'products': products})

      
@login_required
def product_create(request):
    """Créer un nouveau produit - ASSOCIÉ AUTOMATIQUEMENT au tenant"""
    if request.method == 'POST':
        # Inclure request.FILES pour gérer les champs d'image/fichier
        form = ProductForm(request.POST, request.FILES, tenant=request.user.tenant)
        if form.is_valid():
            product = form.save(commit=False)
            product.tenant = request.user.tenant
            product.save()
            messages.success(request, 'Produit ajouté avec succès !')
            return redirect('product_list')
    else:
        form = ProductForm(tenant=request.user.tenant)

    return render(request, 'products/product_form.html', {'form': form})


@login_required
def product_update(request, pk):
    """Modifier un produit - VÉRIFICATION AUTOMATIQUE du tenant"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        # Inclure request.FILES pour gérer les champs d'image/fichier
        form = ProductForm(request.POST, request.FILES, instance=product, tenant=request.user.tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produit modifié avec succès !')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product, tenant=request.user.tenant)
    
    return render(request, 'products/product_form.html', {'form': form})


@login_required
def product_delete(request, pk):
    """Supprimer un produit - VÉRIFICATION AUTOMATIQUE du tenant"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Produit supprimé avec succès !')
        return redirect('product_list')
    
    return render(request, 'products/product_confirm_delete.html', {'product': product})



def login(request):
    """
    Handle user login with tenant session management.
    """
    from django.contrib.auth import authenticate, login as auth_login
    from .forms import TenantAwareAuthenticationForm

    if request.method == 'POST':
        form = TenantAwareAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # ✅ Check if user has a tenant
            if not user.tenant:
                messages.error(request, 'Votre compte n\'est pas associé à un tenant.')
                return redirect('login')
            
            # ✅ Store tenant in session BEFORE logging in
            request.session['tenant_id'] = user.tenant.id
            request.session['tenant_domain'] = user.tenant.domain
            
            # Log in the user
            auth_login(request, user)
            
            messages.success(request, f'Bienvenue {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe invalide.')
    else:
        form = TenantAwareAuthenticationForm()

    return render(request, 'login.html', {'form': form})


def register(request):
    """
    Handle user registration with AUTO-LOGIN and tenant session.
    """
    from django.contrib.auth import login as auth_login
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            try:
                # Save user and create tenant
                user = form.save()
                
                # ✅ Make sure tenant was created
                if not user.tenant:
                    messages.error(request, 'Erreur lors de la création du compte.')
                    return redirect('register')
                
                # ✅ Store tenant in session BEFORE logging in
                request.session['tenant_id'] = user.tenant.id
                request.session['tenant_domain'] = user.tenant.domain
                
                # ✅ Automatically log in the user with explicit backend
                auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                messages.success(
                    request, 
                    f'Bienvenue {user.username}! Votre compte a été créé avec succès.'
                )
                
                return redirect('dashboard')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de la création du compte: {str(e)}')
                return redirect('register')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})

def logout_view(request):
    """
    Log out the user and redirect to login page.
    """
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')
@login_required
def account(request):
    """Account settings page"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Update profile information
        if action == 'update_profile':
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            
            user = request.user
            
            # Check if username is taken by another user
            if username != user.username:
                from django.contrib.auth.models import User
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'Ce nom d\'utilisateur est déjà pris.')
                    return redirect('account')
            
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            messages.success(request, 'Profil mis à jour avec succès!')
            return redirect('account')
        
        # Change password
        elif action == 'change_password':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Mot de passe changé avec succès!')
                return redirect('account')
            else:
                for error in form.errors.values():
                    messages.error(request, error)
                return redirect('account')
    
    context = {
        'user': request.user,
    }
    return render(request, 'account.html', context)

@login_required
def client_list(request):
    """Liste des clients - FILTRÉS AUTOMATIQUEMENT par tenant"""
    clients = Client.objects.all().order_by('-created_at')
    return render(request, 'clients/client_list.html', {'clients': clients})
@login_required
def client_create(request):
    """Créer un nouveau client - ASSOCIÉ AUTOMATIQUEMENT au tenant"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.tenant = request.user.tenant
            client.save()
            messages.success(request, 'Client ajouté avec succès !')
            return redirect('client_list')
    else:
        form = ClientForm()

    return render(request, 'clients/client_form.html', {'form': form})
@login_required
def client_delete(request, pk):
    """Supprimer un client - VÉRIFICATION AUTOMATIQUE du tenant"""
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Client supprimé avec succès !')
        return redirect('client_list')
    
    return render(request, 'clients/client_confirm_delete.html', {'client': client})




def order_list(request):
    # Récupérer toutes les commandes
    orders = Order.objects.all().select_related('client').order_by('-created_at')
    
    # Recherche
    search = request.GET.get('search', '')
    if search:
        orders = orders.filter(
            Q(id__icontains=search) |
            Q(client__name__icontains=search) |
            Q(client__phone__icontains=search)
        )
    
    # Filtre par statut
    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)
    
    # Filtre par mode de livraison
    delivery_mode = request.GET.get('delivery_mode', '')
    if delivery_mode:
        orders = orders.filter(delivery_mode=delivery_mode)
    
    # Statistiques (sur toutes les commandes, pas filtrées)
    total_revenue = Order.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Pagination (20 commandes par page)
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_revenue': total_revenue,
    }
    
    return render(request, 'orders/order_list.html', context)
    orders = Order.objects.all().select_related('client')
    
    # Recherche
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(id__icontains=search) |
            Q(client__name__icontains=search) |
            Q(client__phone__icontains=search)
        )
    
    # Filtres
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    delivery_mode = request.GET.get('delivery_mode')
    if delivery_mode:
        orders = orders.filter(delivery_mode=delivery_mode)
    
    # Pagination (20 par page)
    paginator = Paginator(orders, 20)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    
    return render(request, 'orders/order_list.html', {
        'orders': orders,
        'total_orders': Order.objects.count(),
        'total_revenue': Order.objects.aggregate(Sum('total_amount'))['total_amount__sum']
    })

@login_required
def order_detail(request, pk):
    """Détail d'une commande - VÉRIFICATION AUTOMATIQUE du tenant"""
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/order_detail.html', {'order': order})



@login_required
def order_create(request):
    """Créer une nouvelle commande - ASSOCIÉE AUTOMATIQUEMENT au tenant"""
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            client_id = request.POST.get('client')
            delivery_mode = request.POST.get('delivery_mode', 'retrait')
            delivery_fee = Decimal(request.POST.get('delivery_fee', 0))
            
            # Récupérer les produits et quantités
            product_ids = request.POST.getlist('products[]')
            quantities = request.POST.getlist('quantities[]')
            
            # Validation
            if not client_id:
                messages.error(request, 'Veuillez sélectionner un client.')
                raise ValueError('Client non sélectionné')
            
            if not product_ids or not quantities:
                messages.error(request, 'Veuillez ajouter au moins un produit.')
                raise ValueError('Aucun produit sélectionné')
            
            # ⭐ FIX: Récupérer le client FILTRÉ PAR TENANT
            client = get_object_or_404(Client, pk=client_id, tenant=request.user.tenant)
            
            # Créer la commande dans une transaction
            with transaction.atomic():
                # Calculer le montant total
                total_amount = Decimal(0)
                
                # Créer la commande
                order = Order.objects.create(
                    tenant=request.user.tenant,
                    client=client,
                    delivery_mode=delivery_mode,
                    delivery_fee=delivery_fee,
                    status='pending',
                    total_amount=0  # Sera mis à jour après
                )
                
                # Créer les items de commande
                for product_id, quantity in zip(product_ids, quantities):
                    if product_id and quantity:
                        # ⭐ FIX: Récupérer le produit FILTRÉ PAR TENANT
                        product = get_object_or_404(
                            Product, 
                            pk=product_id, 
                            tenant=request.user.tenant
                        )
                        qty = int(quantity)
                        
                        # Vérifier le stock
                        if product.stock < qty:
                            messages.error(
                                request, 
                                f'Stock insuffisant pour {product.name}. Stock disponible: {product.stock}'
                            )
                            raise ValueError('Stock insuffisant')
                        
                        # Créer l'item de commande
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=qty,
                            price=product.price
                        )
                        
                        # Mettre à jour le stock
                        product.stock -= qty
                        product.save()
                        
                        # Ajouter au total
                        total_amount += product.price * qty
                
                # Ajouter les frais de livraison au total
                total_amount += delivery_fee
                
                # Mettre à jour le montant total de la commande
                order.total_amount = total_amount
                order.save()
                
                messages.success(request, f'Commande #{order.id} créée avec succès !')
                return redirect('order_list')
                
        except ValueError as e:
            # Erreur de validation - retourner au formulaire
            pass
        except Exception as e:
            messages.error(request, f'Erreur lors de la création de la commande: {str(e)}')
    
    # GET request ou erreur - afficher le formulaire
    # ⭐ FIX: Filtrer les produits et clients par tenant
    products_list = [
        {
            'id': p.id,
            'name': p.name,
            'price': float(p.price),
            'stock': p.stock
        }
        for p in Product.objects.filter(
            tenant=request.user.tenant,
            stock__gt=0
        ).order_by('name')
    ]
    
    context = {
        'clients': Client.objects.filter(tenant=request.user.tenant).order_by('name'),
        'products': products_list,
    }
    return render(request, 'orders/order_form.html', context)


@login_required
@require_http_methods(["POST"])
def client_create_ajax(request):
    """Créer un client via AJAX depuis le formulaire de commande"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        area = data.get('area', '').strip()
        
        if not name or not phone:
            return JsonResponse({
                'success': False,
                'error': 'Le nom et le téléphone sont obligatoires'
            })
        
        # ⭐ Vérifier si le client existe déjà POUR CE TENANT
        if Client.objects.filter(tenant=request.user.tenant, phone=phone).exists():
            return JsonResponse({
                'success': False,
                'error': 'Un client avec ce numéro existe déjà'
            })
        
        # ⭐ Créer le client ASSOCIÉ AU TENANT
        client = Client.objects.create(
            tenant=request.user.tenant,
            name=name,
            phone=phone,
            area=area
        )
        
        return JsonResponse({
            'success': True,
            'client': {
                'id': client.id,
                'name': client.name,
                'phone': client.phone,
                'area': client.area or ''
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def order_delete(request, pk):
    """Supprimer une commande - VÉRIFICATION AUTOMATIQUE du tenant"""
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        # Optionnel: Restaurer le stock des produits
        with transaction.atomic():
            for item in order.items.all():
                product = item.product
                product.stock += item.quantity
                product.save()
            
            order.delete()
        
        messages.success(request, 'Commande supprimée avec succès !')
        return redirect('order_list')
    
    return render(request, 'orders/order_confirm_delete.html', {'order': order})


@login_required
def order_update_status(request, pk):
    """Mettre à jour le statut d'une commande"""
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        if new_status in ['pending', 'in_progress', 'delivered']:
            order.status = new_status
            order.save()
            
            status_labels = {
                'pending': 'En attente',
                'in_progress': 'En cours',
                'delivered': 'Livré'
            }
            
            messages.success(
                request, 
                f'Statut de la commande mis à jour: {status_labels.get(new_status)}'
            )
        else:
            messages.error(request, 'Statut invalide.')
    
    return redirect('order_detail', pk=pk)

@login_required
def order_update(request, pk):
    """Mettre à jour une commande existante - VÉRIFICATION AUTOMATIQUE du tenant"""
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            client_id = request.POST.get('client')
            delivery_mode = request.POST.get('delivery_mode', 'retrait')
            delivery_fee = Decimal(request.POST.get('delivery_fee', 0))
            
            # Récupérer les produits et quantités
            product_ids = request.POST.getlist('products[]')
            quantities = request.POST.getlist('quantities[]')
            
            # Validation
            if not client_id:
                messages.error(request, 'Veuillez sélectionner un client.')
                raise ValueError('Client non sélectionné')
            
            if not product_ids or not quantities:
                messages.error(request, 'Veuillez ajouter au moins un produit.')
                raise ValueError('Aucun produit sélectionné')
            
            # Récupérer le client
            client = get_object_or_404(Client, pk=client_id)
            
            # Mettre à jour la commande dans une transaction
            with transaction.atomic():
                # Restaurer le stock des anciens items
                for item in order.items.all():
                    product = item.product
                    product.stock += item.quantity
                    product.save()
                
                # Supprimer les anciens items
                order.items.all().delete()
                
                # Calculer le nouveau montant total
                total_amount = Decimal(0)
                
                # Mettre à jour les détails de la commande
                order.client = client
                order.delivery_mode = delivery_mode
                order.delivery_fee = delivery_fee
                
                # Créer les nouveaux items de commande
                for product_id, quantity in zip(product_ids, quantities):
                    if product_id and quantity:
                        product = get_object_or_404(Product, pk=product_id)
                        qty = int(quantity)
                        
                        # Vérifier le stock
                        if product.stock < qty:
                            messages.error(
                                request, 
                                f'Stock insuffisant pour {product.name}. Stock disponible: {product.stock}'
                            )
                            raise ValueError('Stock insuffisant')
                        
                        # Créer l'item de commande
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=qty,
                            price=product.price
                        )
                        
                        # Mettre à jour le stock
                        product.stock -= qty
                        product.save()

                        # Ajouter au total
                        total_amount += product.price * qty
                
                # Ajouter les frais de livraison au total
                total_amount += delivery_fee
                
                # Mettre à jour le montant total de la commande
                order.total_amount = total_amount
                order.save()
                
                messages.success(request, f'Commande #{order.id} mise à jour avec succès !')
                return redirect('order_detail', pk=order.pk)
                
        except ValueError:
            # Erreur de validation - retourner au formulaire
            pass
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour de la commande: {str(e)}')
    
    # GET request ou erreur - afficher le formulaire
    products_list = [
        {
            'id': p.id,
            'name': p.name,
            'price': float(p.price),
            'stock': p.stock
        }
        for p in Product.objects.filter(stock__gt=0).order_by('name')
    ]
    
    context = {
        'order': order,
        'clients': Client.objects.all().order_by('name'),
        'products': products_list,
    }
    return render(request, 'orders/order_form.html', context)                 


    # views.py



    """Créer un client via AJAX depuis le formulaire de commande"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        area = data.get('area', '').strip()
        
        if not name or not phone:
            return JsonResponse({
                'success': False,
                'error': 'Le nom et le téléphone sont obligatoires'
            })
        
        # Vérifier si le client existe déjà
        if Client.objects.filter(phone=phone).exists():
            return JsonResponse({
                'success': False,
                'error': 'Un client avec ce numéro existe déjà'
            })
        
        # Créer le client
        client = Client.objects.create(
            name=name,
            phone=phone,
            area=area
        )
        
        return JsonResponse({
            'success': True,
            'client': {
                'id': client.id,
                'name': client.name,
                'phone': client.phone,
                'area': client.area or ''
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })