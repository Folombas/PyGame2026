import json
from meta import save_meta

# card: id, name_key, desc_key, rarity (0=common,1=rare,2=epic,3=legendary), stat, threshold
CARDS = [
    {'id': 'c1',  'name_key': 'cname1',  'desc_key': 'cdesc1',  'rarity': 0, 'stat': 'total_lines', 'threshold': 10},
    {'id': 'c2',  'name_key': 'cname2',  'desc_key': 'cdesc2',  'rarity': 0, 'stat': 'total_lines', 'threshold': 50},
    {'id': 'c3',  'name_key': 'cname3',  'desc_key': 'cdesc3',  'rarity': 0, 'stat': 'best_score', 'threshold': 1000},
    {'id': 'c4',  'name_key': 'cname4',  'desc_key': 'cdesc4',  'rarity': 0, 'stat': 'best_score', 'threshold': 5000},
    {'id': 'c5',  'name_key': 'cname5',  'desc_key': 'cdesc5',  'rarity': 0, 'stat': 'best_level', 'threshold': 3},
    {'id': 'c6',  'name_key': 'cname6',  'desc_key': 'cdesc6',  'rarity': 1, 'stat': 'total_lines', 'threshold': 200},
    {'id': 'c7',  'name_key': 'cname7',  'desc_key': 'cdesc7',  'rarity': 1, 'stat': 'best_score', 'threshold': 15000},
    {'id': 'c8',  'name_key': 'cname8',  'desc_key': 'cdesc8',  'rarity': 1, 'stat': 'best_level', 'threshold': 8},
    {'id': 'c9',  'name_key': 'cname9',  'desc_key': 'cdesc9',  'rarity': 1, 'stat': 'tetris_count', 'threshold': 10},
    {'id': 'c10', 'name_key': 'cname10', 'desc_key': 'cdesc10', 'rarity': 1, 'stat': 'max_combo', 'threshold': 5},
    {'id': 'c11', 'name_key': 'cname11', 'desc_key': 'cdesc11', 'rarity': 2, 'stat': 'total_lines', 'threshold': 500},
    {'id': 'c12', 'name_key': 'cname12', 'desc_key': 'cdesc12', 'rarity': 2, 'stat': 'best_score', 'threshold': 30000},
    {'id': 'c13', 'name_key': 'cname13', 'desc_key': 'cdesc13', 'rarity': 2, 'stat': 'best_level', 'threshold': 12},
    {'id': 'c14', 'name_key': 'cname14', 'desc_key': 'cdesc14', 'rarity': 2, 'stat': 'tetris_count', 'threshold': 50},
    {'id': 'c15', 'name_key': 'cname15', 'desc_key': 'cdesc15', 'rarity': 2, 'stat': 'longest_run', 'threshold': 600},
    {'id': 'c16', 'name_key': 'cname16', 'desc_key': 'cdesc16', 'rarity': 3, 'stat': 'total_lines', 'threshold': 1000},
    {'id': 'c17', 'name_key': 'cname17', 'desc_key': 'cdesc17', 'rarity': 3, 'stat': 'best_score', 'threshold': 75000},
    {'id': 'c18', 'name_key': 'cname18', 'desc_key': 'cdesc18', 'rarity': 3, 'stat': 'best_level', 'threshold': 18},
    {'id': 'c19', 'name_key': 'cname19', 'desc_key': 'cdesc19', 'rarity': 3, 'stat': 'tetris_count', 'threshold': 100},
    {'id': 'c20', 'name_key': 'cname20', 'desc_key': 'cdesc20', 'rarity': 3, 'stat': 'max_combo', 'threshold': 10},
]

RARITY_NAMES = ['Common', 'Rare', 'Epic', 'Legendary']
RARITY_COLORS = [(160, 160, 180), (60, 160, 240), (170, 80, 240), (255, 200, 50)]

def get_card_by_id(cid):
    return next((c for c in CARDS if c['id'] == cid), None)

def check_unlocks(meta):
    owned = set(meta.get('cards', []))
    new = []
    for c in CARDS:
        if c['id'] in owned: continue
        if meta['stats'].get(c['stat'], 0) >= c['threshold']:
            meta['cards'].append(c['id'])
            new.append(c['id'])
    if new:
        save_meta(meta)
    return new
