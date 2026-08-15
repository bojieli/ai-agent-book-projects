class Catalog:
    def __init__(self, cache, fetch_product):
        self.cache = cache
        self.fetch_product = fetch_product

    def product(self, product_id):
        return self.cache.get_or_load(product_id, self.fetch_product)
