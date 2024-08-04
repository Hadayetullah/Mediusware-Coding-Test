from django.views import generic

from product.models import Variant, Product, ProductVariantPrice


class CreateProductView(generic.TemplateView):
    template_name = 'products/create.html'

    def get_context_data(self, **kwargs):
        context = super(CreateProductView, self).get_context_data(**kwargs)
        variants = Variant.objects.filter(active=True).values('id', 'title')
        context['product'] = True
        context['variants'] = list(variants.all())
        return context
    
    

class ProductListView(generic.ListView):
    template_name = 'products/list.html'
    context_object_name = 'products'

    def get_queryset(self):
        queryset = Product.objects.all()

        # Apply filters if any
        title = self.request.GET.get('title')
        variant = self.request.GET.get('variant')
        price_from = self.request.GET.get('price_from')
        price_to = self.request.GET.get('price_to')
        date = self.request.GET.get('date')

        if title:
            queryset = queryset.filter(title__icontains(title))
        if variant:
            queryset = queryset.filter(productvariantprice__product_variant_one__variant_title__icontains(variant) |
                                       productvariantprice__product_variant_two__variant_title__icontains(variant) |
                                       productvariantprice__product_variant_three__variant_title__icontains(variant)).distinct()
        if price_from:
            queryset = queryset.filter(productvariantprice__price__gte=price_from)
        if price_to:
            queryset = queryset.filter(productvariantprice__price__lte=price_to)
        if date:
            queryset = queryset.filter(created_at__date=date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data(**kwargs)
        products = self.get_queryset()
        product_list = []

        for product in products:
            variants = ProductVariantPrice.objects.filter(product=product)
            variant_list = []

            for variant in variants:
                variant_data = {
                    'variant_title_one': variant.product_variant_one.variant_title if variant.product_variant_one else None,
                    'variant_title_two': variant.product_variant_two.variant_title if variant.product_variant_two else None,
                    'variant_title_three': variant.product_variant_three.variant_title if variant.product_variant_three else None,
                    'price': variant.price,
                    'stock': variant.stock,
                }
                variant_list.append(variant_data)

            product_data = {
                'title': product.title,
                'description': product.description,
                'created_at': product.created_at,
                'variants': variant_list,
            }
            product_list.append(product_data)

        context['product'] = True
        context['products'] = product_list

        print(context)
        return context