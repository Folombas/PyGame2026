# Pack pricing and purchase logic
PACK_PRICES = {
    'standard': 200,   # 1 random card
    'premium': 800,    # guaranteed rare+
    'legendary': 2500, # guaranteed legendary chance x5
}

def can_afford(meta, kind):
    return meta.get('coins', 0) >= PACK_PRICES.get(kind, 999999)

def buy_pack(meta, kind):
    """Returns True if purchased."""
    price = PACK_PRICES.get(kind)
    if not price or meta.get('coins', 0) < price:
        return False
    meta['coins'] -= price
    meta['unopened_packs'] = meta.get('unopened_packs', 0) + 1
    meta['_last_buy_kind'] = kind
    from meta import save_meta
    save_meta(meta)
    return True
