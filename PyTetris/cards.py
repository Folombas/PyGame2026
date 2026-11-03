import random
from meta import save_meta

RARITY_NAMES = ['Common', 'Rare', 'Epic', 'Legendary']
RARITY_COLORS = [(160, 160, 180), (60, 160, 240), (170, 80, 240), (255, 200, 50)]
RARITY_WEIGHTS = [60, 25, 12, 3]

CATEGORIES = ['beasts', 'lands', 'artifacts', 'signs', 'heroes']

# 20 cards, 5 per category, ascending rarity
CARDS = [
    # beasts
    {'id': 'b1', 'name_key': 'cname1',  'rarity': 0, 'cat': 'beasts',   'stat': 'total_lines', 'threshold': 10},
    {'id': 'b2', 'name_key': 'cname2',  'rarity': 1, 'cat': 'beasts',   'stat': 'total_lines', 'threshold': 100},
    {'id': 'b3', 'name_key': 'cname3',  'rarity': 2, 'cat': 'beasts',   'stat': 'max_combo',   'threshold': 8},
    {'id': 'b4', 'name_key': 'cname4',  'rarity': 3, 'cat': 'beasts',   'stat': 'tetris_count','threshold': 75},
    # lands
    {'id': 'l1', 'name_key': 'cname5',  'rarity': 0, 'cat': 'lands',    'stat': 'best_level', 'threshold': 3},
    {'id': 'l2', 'name_key': 'cname6',  'rarity': 1, 'cat': 'lands',    'stat': 'best_level', 'threshold': 8},
    {'id': 'l3', 'name_key': 'cname7',  'rarity': 2, 'cat': 'lands',    'stat': 'best_score', 'threshold': 30000},
    {'id': 'l4', 'name_key': 'cname8',  'rarity': 3, 'cat': 'lands',    'stat': 'best_score', 'threshold': 100000},
    # artifacts
    {'id': 'a1', 'name_key': 'cname9',  'rarity': 0, 'cat': 'artifacts','stat': 'best_score', 'threshold': 1000},
    {'id': 'a2', 'name_key': 'cname10', 'rarity': 1, 'cat': 'artifacts','stat': 'best_score', 'threshold': 15000},
    {'id': 'a3', 'name_key': 'cname11', 'rarity': 2, 'cat': 'artifacts','stat': 'longest_run', 'threshold': 600},
    {'id': 'a4', 'name_key': 'cname12', 'rarity': 3, 'cat': 'artifacts','stat': 'total_lines', 'threshold': 1500},
    # signs
    {'id': 's1', 'name_key': 'cname13', 'rarity': 0, 'cat': 'signs',    'stat': 'hold_uses', 'threshold': 10},
    {'id': 's2', 'name_key': 'cname14', 'rarity': 1, 'cat': 'signs',    'stat': 'b2b_count', 'threshold': 5},
    {'id': 's3', 'name_key': 'cname15', 'rarity': 2, 'cat': 'signs',    'stat': 'sprint_wins', 'threshold': 10},
    {'id': 's4', 'name_key': 'cname16', 'rarity': 3, 'cat': 'signs',    'stat': 'max_combo', 'threshold': 10},
    # heroes
    {'id': 'h1', 'name_key': 'cname17', 'rarity': 0, 'cat': 'heroes',   'stat': 'total_lines', 'threshold': 50},
    {'id': 'h2', 'name_key': 'cname18', 'rarity': 1, 'cat': 'heroes',   'stat': 'tetris_count','threshold': 10},
    {'id': 'h3', 'name_key': 'cname19', 'rarity': 2, 'cat': 'heroes',   'stat': 'best_level', 'threshold': 12},
    {'id': 'h4', 'name_key': 'cname20', 'rarity': 3, 'cat': 'heroes',   'stat': 'zen_games',  'threshold': 50},
]

def get_card_by_id(cid):
    return next((c for c in CARDS if c['id'] == cid), None)

def get_cards_by_category(cat):
    return [c for c in CARDS if c['cat'] == cat]

def check_unlocks(meta):
    owned = meta.get('cards', {})
    new = []
    for c in CARDS:
        if c['id'] in owned: continue
        if meta['stats'].get(c['stat'], 0) >= c['threshold']:
            owned[c['id']] = 1
            new.append(c['id'])
    if new:
        meta['cards'] = owned
        save_meta(meta)
    return new

def open_pack(meta):
    if meta.get('unopened_packs', 0) <= 0:
        return None
    meta['unopened_packs'] -= 1

    rarities, weights = rarity_weights_with_featured()
    rarity = random.choices(rarities, weights=weights)[0]
    candidates = [c for c in CARDS if c['rarity'] == rarity]
    if not candidates:
        candidates = [c for c in CARDS if c['rarity'] == 0]
    card = random.choice(candidates)

    # Foil: 5% chance overall, 15% if featured
    foil_chance = 0.15 if is_featured(card) else 0.05
    is_foil = random.random() < foil_chance

    cards = meta.get('cards', {})
    if card['id'] in cards:
        meta.setdefault('card_dups', {})
        meta['card_dups'][card['id']] = meta['card_dups'].get(card['id'], 0) + 1
        levels = 1 + meta['card_dups'][card['id']] // 3
        meta['cards'][card['id']] = min(5, levels)
        result = {'card_id': card['id'], 'duplicate': True, 'foil': False, 'new_level': meta['cards'][card['id']]}
    else:
        meta['cards'][card['id']] = 1
        result = {'card_id': card['id'], 'duplicate': False, 'foil': is_foil, 'new_level': 1}
        if is_foil:
            meta.setdefault('foil_cards', {})
            meta['foil_cards'][card['id']] = True

    # Check sets after new card
    new_sets = check_completed_sets(meta)
    result['new_sets'] = new_sets

    save_meta(meta)
    return result

def get_card_level(meta, cid):
    return meta.get('cards', {}).get(cid, 0)

def get_card_dups_to_next(meta, cid):
    if cid not in meta.get('card_dups', {}):
        return 3
    return 3 - (meta['card_dups'][cid] % 3)


CARD_SETS = {
    'beasts':    {'name_key': 'set_beasts',    'cards': ['b1', 'b2', 'b3', 'b4'], 'packs': 3, 'xp': 100},
    'lands':     {'name_key': 'set_lands',     'cards': ['l1', 'l2', 'l3', 'l4'], 'packs': 3, 'xp': 100},
    'artifacts': {'name_key': 'set_artifacts', 'cards': ['a1', 'a2', 'a3', 'a4'], 'packs': 3, 'xp': 100},
    'signs':     {'name_key': 'set_signs',     'cards': ['s1', 's2', 's3', 's4'], 'packs': 3, 'xp': 100},
    'heroes':    {'name_key': 'set_heroes',    'cards': ['h1', 'h2', 'h3', 'h4'], 'packs': 3, 'xp': 100},
}

def check_completed_sets(meta):
    cards = meta.get('cards', {})
    done = set(meta.get('completed_sets', []))
    new = []
    for cat, s in CARD_SETS.items():
        if cat in done: continue
        if all(c in cards for c in s['cards']):
            done.add(cat)
            meta['unopened_packs'] = meta.get('unopened_packs', 0) + s['packs']
            meta['xp'] = meta.get('xp', 0) + s['xp']
            new.append(cat)
    if new:
        meta['completed_sets'] = list(done)
        save_meta(meta)
    return new

def get_set_progress(meta, cat):
    s = CARD_SETS[cat]
    cards = meta.get('cards', {})
    got = sum(1 for c in s['cards'] if c in cards)
    return got, len(s['cards'])


import hashlib
import datetime

def get_featured_card():
    """Rotates daily. Boosted drop rate (2x for its rarity)."""
    today = datetime.date.today().isoformat()
    h = int(hashlib.md5(today.encode()).hexdigest(), 16)
    # Pick a non-common card as featured
    candidates = [c for c in CARDS if c['rarity'] >= 1]
    if not candidates:
        candidates = CARDS
    return candidates[h % len(candidates)]

def is_featured(card):
    return card['id'] == get_featured_card()['id']

def rarity_weights_with_featured():
    """Returns (rarities, weights) with featured card's rarity doubled."""
    feat = get_featured_card()
    weights = list(RARITY_WEIGHTS)
    for i, r in enumerate([0, 1, 2, 3]):
        if r == feat['rarity']:
            weights[i] *= 2
    return [0, 1, 2, 3], weights
