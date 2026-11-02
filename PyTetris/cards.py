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
    """Open one pack: gives 1 random card. Returns card id or None."""
    if meta.get('unopened_packs', 0) <= 0:
        return None
    meta['unopened_packs'] -= 1
    # weighted rarity
    rarities = [0, 1, 2, 3]
    rarity = random.choices(rarities, weights=RARITY_WEIGHTS)[0]
    candidates = [c for c in CARDS if c['rarity'] == rarity]
    if not candidates:
        candidates = [c for c in CARDS if c['rarity'] == 0]
    card = random.choice(candidates)
    cards = meta.get('cards', {})
    if card['id'] in cards:
        # duplicate -> +1 level
        meta['card_dups'][card['id']] = meta['card_dups'].get(card['id'], 0) + 1
        levels = 1 + meta['card_dups'][card['id']] // 3
        meta['cards'][card['id']] = min(5, levels)
    else:
        meta['cards'][card['id']] = 1
    save_meta(meta)
    return card['id']

def get_card_level(meta, cid):
    return meta.get('cards', {}).get(cid, 0)

def get_card_dups_to_next(meta, cid):
    if cid not in meta.get('card_dups', {}):
        return 3
    return 3 - (meta['card_dups'][cid] % 3)
