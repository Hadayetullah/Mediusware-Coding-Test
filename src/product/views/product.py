import json
from django.views import generic
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.http import JsonResponse
from product.models import Variant, Product, ProductVariantPrice, ProductVariant, ProductImage

class CreateProductView(generic.TemplateView):
    template_name = 'products/create.html'

    def get_context_data(self, **kwargs):
        context = super(CreateProductView, self).get_context_data(**kwargs)
        variants = Variant.objects.filter(active=True).values('id', 'title')
        context['product'] = True
        context['variants'] = list(variants.all())
        return context

    def post(self, request, *args, **kwargs):
        data = request.POST
        product = Product.objects.create(
            title=data.get('title'),
            sku=data.get('sku'),
            description=data.get('description')
        )

        # Assuming files are being uploaded
        for file in request.FILES.getlist('files'):
            ProductImage.objects.create(product=product, file_path=file)

        # Product variants
        product_variant_data = data.get('product_variants')
        if product_variant_data:
            for variant in json.loads(product_variant_data):
                ProductVariant.objects.create(
                    product=product,
                    variant_id=variant['option'],
                    variant_title='/'.join(variant['tags'])
                )

        # Product variant prices
        product_variant_price_data = data.get('product_variant_prices')
        if product_variant_price_data:
            for variant_price in json.loads(product_variant_price_data):
                product_variant = ProductVariant.objects.get(variant_title=variant_price['title'])
                ProductVariantPrice.objects.create(
                    product=product,
                    product_variant_one=product_variant,
                    price=variant_price['price'],
                    stock=variant_price['stock']
                )

        return JsonResponse({"message": "Product created successfully"}, status=201)

    

class ProductListView(generic.ListView):
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    paginate_by = 10  # Number of products per page

    def get_queryset(self):
        queryset = Product.objects.all()
        title = self.request.GET.get('title', None)
        variant = self.request.GET.get('variant', None)
        price_from = self.request.GET.get('price_from', None)
        price_to = self.request.GET.get('price_to', None)
        date = self.request.GET.get('date', None)

        if title:
            queryset = queryset.filter(title__icontains=title)
        if variant:
            queryset = queryset.filter(
                Q(productvariantprice__product_variant_one__variant_title=variant) |
                Q(productvariantprice__product_variant_two__variant_title=variant) |
                Q(productvariantprice__product_variant_three__variant_title=variant)
            )
        if price_from or price_to:
            price_filter = Q()
            if price_from:
                price_filter &= Q(productvariantprice__price__gte=float(price_from))
            if price_to:
                price_filter &= Q(productvariantprice__price__lte=float(price_to))
            queryset = queryset.filter(price_filter)
        if date:
            queryset = queryset.filter(created_at__date=date)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        variants = ProductVariant.objects.values_list('variant_title', flat=True).distinct()
        print("Variant: ", variants)
        context['variants'] = variants

        # Group product variants by variant titles
        variant_groups = {}
        for variant in Variant.objects.values_list('title', flat=True).distinct():
            variant_groups[variant] = ProductVariant.objects.filter(variant__title=variant).values_list('variant_title', flat=True).distinct()
        # print("Group: ", variant_groups)

        context['variant_groups'] = variant_groups

        paginator = Paginator(self.get_queryset(), self.paginate_by)
        page = self.request.GET.get('page')
        products = paginator.get_page(page)

        context['products'] = products
        return context