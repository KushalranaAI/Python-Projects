"""Flask interface. The shop lives in memory for this server process (restart = fresh shop); the cart is in the session."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from projects.ui_kit import run_standalone

from .catalog import Cart, ShopError
from .discounts import COUPONS
from .orders import TRANSITIONS
from .shop import Shop

bp = Blueprint("online_shop", __name__, template_folder="templates")
shop = Shop()


def cart() -> Cart:
    return Cart(dict(session.get("shop_cart", {})))


def save_cart(c: Cart) -> None:
    session["shop_cart"] = c.lines


def codes() -> list[str]:
    return session.get("shop_codes", [])


@bp.get("/")
def index():
    c = cart()
    return render_template("online_shop/index.html", shop=shop, cart=c, items=c.items(shop.products), quote=shop.quote(c, codes()),
                           codes=codes(), coupons=COUPONS, orders=sorted(shop.orders.values(), key=lambda o: -o.id),
                           transitions=TRANSITIONS)


@bp.post("/cart")
def update_cart():
    c = cart()
    try:
        sku = request.form["sku"]
        if request.form.get("op") == "add":
            c.add(shop.products[sku])
        else:
            c.set_quantity(sku, int(request.form.get("quantity", 0)))
        save_cart(c)
    except (KeyError, ValueError, ShopError) as error:
        flash(str(error), "error")
    return redirect(url_for(".index"))


@bp.post("/coupon")
def coupon():
    code = request.form.get("code", "").strip().upper()
    if request.form.get("remove"):
        session["shop_codes"] = [c for c in codes() if c != request.form["remove"]]
    elif code in COUPONS:
        session["shop_codes"] = list(dict.fromkeys(codes() + [code]))
        if not COUPONS[code].applies(cart(), shop.products):
            flash(f"{code} saved, but it doesn't apply to this cart yet ({COUPONS[code].description}).", "info")
    else:
        flash(f"Unknown coupon '{code}'.", "error")
    return redirect(url_for(".index"))


@bp.post("/checkout")
def checkout():
    try:
        order = shop.place_order(cart(), codes(), datetime.now())
        session["shop_cart"], session["shop_codes"] = {}, []
        flash(f"Order #{order.id} placed!", "success")
    except ShopError as error:
        flash(str(error), "error")
    return redirect(url_for(".index"))


@bp.post("/orders/<int:order_id>/<action>")
def order_action(order_id: int, action: str):
    try:
        shop.act(order_id, action, datetime.now())
    except ShopError as error:
        flash(str(error), "error")
    return redirect(url_for(".index"))


if __name__ == "__main__":
    run_standalone(bp, "Online Shop")
