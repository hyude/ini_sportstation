import datetime
from django.shortcuts import render, redirect, get_object_or_404
from main.forms import ProductForm
from main.models import Product
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core import serializers
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.utils.html import strip_tags

# Create your views here.
@login_required(login_url='/login')
def show_main(request):
    filter_type = request.GET.get("filter", "all")

    if filter_type == "all":
        product_list = Product.objects.all()
    else:
        product_list = Product.objects.filter(user=request.user)

    context = {
        'npm' : '2406421970',
        'name': request.user.username,
        'class': 'PBP E',
        'product_list': product_list,
        'last_login': request.COOKIES.get('last_login', 'Never')
    }

    return render(request, "main.html", context)

@login_required(login_url='/login')
def create_product(request):
    form = ProductForm(request.POST or None)

    if form.is_valid() and request.method == "POST":
        product_entry = form.save(commit=False)
        product_entry.user = request.user
        product_entry.save()
        return redirect('main:show_main')
    
    context = {
        'form': form
    }

    return render(request, "create_product.html", context)

@login_required(login_url='/login')
def show_product(request, id):
    product = get_object_or_404(Product, pk=id)

    context = {
        'product': product
    }

    return render(request, "product_details.html", context)

def show_xml(request):
    product_list = Product.objects.all()
    xml_data = serializers.serialize("xml", product_list)
    return HttpResponse(xml_data, content_type="application/xml")

def show_json(request):
    product_list = Product.objects.all()
    data = [
        {
            'id': str(product.id),
            'name': product.name,
            'price': product.price,
            'description': product.description,
            'thumbnail': product.thumbnail,
            'category': product.category,
            'is_featured': product.is_featured,
            'user_id': product.user_id,
        }
        for product in product_list
    ]

    return JsonResponse(data, safe=False)

def show_xml_by_id(request, product_id):
    try:
        product_item = Product.objects.filter(pk=product_id)
        xml_data = serializers.serialize("xml", product_item)
        return HttpResponse(xml_data, content_type="application/xml")
    except Product.DoesNotExist:
        return HttpResponse(status=404)

def show_json_by_id(request, product_id):
    try:
        product = Product.objects.select_related('user').get(pk=product_id)
        data = {
            'id': str(product.id),
            'name': product.name,
            'price': product.price,
            'description': product.description,
            'thumbnail': product.thumbnail,
            'category': product.category,
            'is_featured': product.is_featured,
            'user_id': product.user_id,
            'user_username': product.user.username if product.user_id else None,
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)
    
def register(request):
    if request.method == 'POST':
        # ambil input
        username = (request.POST.get('username') or '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        # helper: apakah AJAX?
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

        # validasi sederhana
        if not username or not password1 or not password2:
            msg = 'All fields are required.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return render(request, 'register.html')

        if password1 != password2:
            msg = 'Passwords do not match.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return render(request, 'register.html')

        if User.objects.filter(username=username).exists():
            msg = 'Username already exists.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return render(request, 'register.html')

        # gunakan UserCreationForm untuk validasi password complexity
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Welcome, {user.username}!',
                    'redirect_url': reverse('main:login')
                })
            messages.success(request, 'Account created. Please log in.')
            return redirect('main:login')
        else:
            # ambil pesan error pertama
            errors = []
            for field, errs in form.errors.items():
                for e in errs:
                    errors.append(f"{field}: {e}")
            msg = errors[0] if errors else 'Invalid input.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return render(request, 'register.html')

    # GET
    return render(request, 'register.html')

@csrf_exempt
def login_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # AJAX request
            if user is not None:
                login(request, user)
                return JsonResponse({
                    "success": True,
                    "message": f"Welcome back, {user.username}!",
                    "redirect_url": "/"  # ubah ke dashboard/home sesuai kebutuhan
                })
            else:
                return JsonResponse({
                    "success": False,
                    "message": "Invalid username or password."
                })
        else:
            # Regular (non-AJAX) fallback
            if user is not None:
                login(request, user)
                return redirect('/')
            else:
                messages.error(request, "Invalid username or password.")
                return render(request, "login.html")

    return render(request, "login.html")

def logout_user(request):
    if request.method == "POST":
        logout(request)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "redirect_url": reverse("main:login"),
            })
        return redirect("main:login")
    return redirect("main:login")

@login_required(login_url='/login')
def edit_product(request, id):
    product = get_object_or_404(Product, pk=id, user=request.user)
    form = ProductForm(request.POST or None, instance=product)

    if request.method == 'POST':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if form.is_valid():
                form.save()
                return JsonResponse({"success": True})
            else:
                # kembalikan detail error sebagai JSON (serializable)
                errors = { field: [str(e) for e in errs] for field, errs in form.errors.items() }
                return JsonResponse({"success": False, "message": "Validation error", "errors": errors}, status=400)
        elif form.is_valid():
            form.save()
            return redirect('main:show_main')


    return render(request, "edit_product.html", {"form": form, "product": product})

@login_required(login_url='/login')
@require_http_methods(["POST", "DELETE"])
def delete_product(request, id):
    """
    Accepts:
      - DELETE request (AJAX) OR
      - POST with header X-HTTP-Method-Override: DELETE (AJAX-friendly)
    Returns JSON for AJAX, redirect for normal requests.
    """
    product = get_object_or_404(Product, pk=id)

    # permission check: hanya owner yang bisa delete
    if product.user != request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)
        return redirect('main:show_main')

    # support method override
    is_delete = (request.method == 'DELETE') or (request.headers.get('x-http-method-override', '').upper() == 'DELETE')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if is_delete:
            product.delete()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid HTTP method.'}, status=400)

    # fallback untuk non-AJAX (regular form POST)
    if request.method in ['POST', 'DELETE']:
        product.delete()
        return redirect('main:show_main')

    return redirect('main:show_main')

@csrf_exempt
@require_POST
def add_product_entry_ajax(request):
    name = strip_tags(request.POST.get("name")) # strip HTML tags!
    description = strip_tags(request.POST.get("description")) # strip HTML tags!
    category = request.POST.get("category")
    thumbnail = request.POST.get("thumbnail")
    is_featured = request.POST.get("is_featured") == 'on'  # checkbox handling
    user = request.user

    new_product = Product(
        name=name, 
        description=description,
        category=category,
        thumbnail=thumbnail,
        is_featured=is_featured,
        user=user
    )
    new_product.save()

    return HttpResponse(b"CREATED", status=201)

@login_required(login_url='/login')
def get_product_json(request, id):
    product = get_object_or_404(Product, pk=id, user=request.user)
    return JsonResponse({
        "id": str(product.id),
        "name": product.name,
        "price": product.price,
        "description": product.description,
    })