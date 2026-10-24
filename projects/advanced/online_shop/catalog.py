"""Products and the shopping cart."""

from __future__ import annotations

from dataclasses import dataclass, field


class ShopError(Exception):
    pass


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    price: int            # cents
    category: str
    icon: str = "📦"


CATALOG = [
    Product("TSHIRT", "Python T-shirt", 2000, "clothing", "👕"),
    Product("HOODIE", "Hoodie", 4500, "clothing", "🧥"),
    Product("MUG", "Coffee mug", 1200, "kitchen", "☕"),
    Product("STICKERS", "Sticker pack", 500, "accessories", "🏷️"),
    Product("BOOK", "Clean Code book", 3500, "books", "📘"),
    Product("KEYBOARD", "Mechanical keyboard", 8900, "electronics", "⌨️"),
]


@dataclass
class Cart:
    lines: dict[str, int] = field(default_factory=dict)      # sku -> quantity

    def add(self, product: Product, quantity: int = 1) -> None:
        if quantity <= 0:
            raise ShopError("Quantity must be positive.")
        self.lines[product.sku] = self.lines.get(product.sku, 0) + quantity

    def set_quantity(self, sku: str, quantity: int) -> None:
        if quantity <= 0:
            self.lines.pop(sku, None)
        else:
            self.lines[sku] = quantity

    def items(self, products: dict[str, Product]) -> list[tuple[Product, int]]:
        return [(products[sku], qty) for sku, qty in self.lines.items()]

    def subtotal(self, products: dict[str, Product]) -> int:
        return sum(p.price * q for p, q in self.items(products))

    @property
    def is_empty(self) -> bool:
        return not self.lines
