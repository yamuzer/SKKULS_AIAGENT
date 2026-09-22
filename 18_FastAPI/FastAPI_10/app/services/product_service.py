from app.schemas.product import ProductCreate


class ProductService:
    def __init__(self) -> None:
        self._products: list[dict] = [
            {
                'id': 1,
                'name': 'Laptop',
                'price': 1_500_000,
                'category': 'computer',
                'quantity': 10
            },
            
            {
                'id': 2,
                'name': 'Keyboard',
                'price': 80_000,
                'category': 'computer',
                'quantity': 30
            },

            {
                'id': 3,
                'name': 'FastAPI book',
                'price': 42_000,
                'category': 'book',
                'quantity': 20
            },

            {
                'id': 4,
                'name': 'AI Course',
                'price': 1_200_000,
                'category': 'education',
                'quantity': 15
            }

        ]


    def list_products(
            self,
            category: str | None = None,
            limit: int = 2
        ) ->list[dict]:
    
        result = self._products.copy()

        if category is not None:
            result = [
                product
                for product in result
                if product['category'] == category
            ]

        return result[: limit]



    def get_product(self, product_id: int) -> dict | None:
    
        for product in self._products:
            if product['id'] == product_id:
                return product

        return None


    def create_product(self, product: ProductCreate) -> dict:
    
        normalized_name = product.name.strip().lower()

        for stored_product in self._products:
            if stored_product['name'].strip().lower() == normalized_name:
                raise ValueError(
                    '같은 이름의 제품이 이미 존재합니다.'
                )

        new_product = {
            'id': self._get_next_id(),
            **product.model_dump()
        }

        self._products.append(new_product)

        return new_product


    def update_product(
            self,
            product_id: int,
            product: ProductCreate
    ) -> dict | None:
    
        stored_product = self.get_product(product_id)

        if stored_product is None:
            return None

        
        stored_product.clear()
        stored_product.update(
            {
                'id': product_id,
                **product.model_dump()
            }
        )

        return stored_product


    def delete_product(self, product_id: int) -> bool:
    
        product = self.get_product(product_id)

        if product is None:
            return False

        self._products.remove(product)

        return True



    def _get_next_id(self) -> int:
        if not self._products:
            return 1

        max_id = max(
            product['id']
            for product in self._products
        )

        return max_id + 1



    



    



    



    
        


    
