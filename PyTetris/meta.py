import json, os, hashlib, datetime
import i18n as locale
from settings import SCORES_FILE, META_FILE

ACHIEVEMENTS = [
    {'id': 'first_clear', 'name_key': 'ach1', 'desc_key': 'achd1',
     'stat': 'total_lines', 'bronze': 1, 'silver': 100, 'gold': 500},
    {'id': 'tetris', 'name_key': 'ach2', 'desc_key': 'achd2',
     'stat': 'tetris_count', 'bronze': 1, 'silver': 10, 'gold': 50},
    {'id': 'combo3', 'name_key': 'ach3', 'desc_key': 'achd3',
     'stat': 'max_combo', 'bronze': 2, 'silver': 5, 'gold': 10},
    {'id': 'combo5', 'name_key': 'ach4', 'desc_key': 'achd4',
     'stat': 'max_combo', 'bronze': 4, 'silver': 8, 'gold': 15},
    {'id': 'level5', 'name_key': 'ach5', 'desc_key': 'achd5',
     'stat': 'best_level', 'bronze': 5, 'silver': 10, 'gold': 15},
    {'id': 'level10', 'name_key': 'ach6', 'desc_key': 'achd6',
     'stat': 'best_level', 'bronze': 10, 'silver': 15, 'gold': 20},
    {'id': 'score5k', 'name_key': 'ach7', 'desc_key': 'achd7',
     'stat': 'best_score', 'bronze': 5000, 'silver': 20000, 'gold': 50000},
    {'id': 'score20k', 'name_key': 'ach8', 'desc_key': 'achd8',
     'stat': 'best_score', 'bronze': 20000, 'silver': 50000, 'gold': 100000},
    {'id': 'marathon', 'name_key': 'ach9', 'desc_key': 'achd9',
     'stat': 'longest_run', 'bronze': 60, 'silver': 300, 'gold': 900},
    {'id': 'lines50', 'name_key': 'ach10', 'desc_key': 'achd10',
     'stat': 'total_lines', 'bronze': 50, 'silver': 250, 'gold': 1000},
]

def _default_meta():
    return {
        'lang': 'en',
        'stats': {'total_lines': 0, 'best_score': 0, 'best_level': 1,
                  'max_combo': 0, 'tetris_count': 0, 'longest_run': 0},
        'unlocked': {}, 'medals': {}, 'cards': [],
        'player_level': 1, 'xp': 0, 'xp_needed': 100,
        'best_sprint_time': 999999.0, 'dailies': {},
        'daily_streak': 0, 'last_daily_date': '',
        'best_score': 0, 'total_lines': 0, 'total_playtime': 0.0,
    }

def _ensure_dir():
    os.makedirs(os.path.dirname(META_FILE), exist_ok=True)

def load_meta():
    _ensure_dir()
    base = _default_meta()
    if os.path.exists(META_FILE):
        try:
            with open(META_FILE) as f:
                data = json.load(f)
            for k, v in data.items():
                if k == 'stats' and isinstance(v, dict):
                    base['stats'].update(v)
                else:
                    base[k] = v
        except Exception:
            pass
    return base

def save_meta(meta):
    _ensure_dir()
    with open(META_FILE, 'w') as f:
        json.dump(meta, f, indent=2)

def get_medal_tier(meta, ach):
    val = meta['stats'].get(ach['stat'], 0)
    if val >= ach['gold']: return 3
    if val >= ach['silver']: return 2
    if val >= ach['bronze']: return 1
    return 0

def get_progress(meta, ach):
    val = meta['stats'].get(ach['stat'], 0)
    for tier, key in [(3, 'gold'), (2, 'silver'), (1, 'bronze')]:
        if val < ach[key]:
            return val, ach[key], tier - 1
    return val, ach['gold'], 3

def check_new_medals(meta):
    new = []
    for a in ACHIEVEMENTS:
        nt = get_medal_tier(meta, a)
        ot = meta['medals'].get(a['id'], 0)
        if nt > ot:
            meta['medals'][a['id']] = nt
            meta['unlocked'][a['id']] = True
            new.append((a['id'], nt))
    if new:
        save_meta(meta)
    return new

def check_run(meta, game, run_time):
    s = meta['stats']
    s['best_score'] = max(s['best_score'], game.score)
    s['best_level'] = max(s['best_level'], game.level)
    s['longest_run'] = max(s['longest_run'], int(run_time))
    meta['best_score'] = s['best_score']
    meta['total_lines'] = s['total_lines']
    meta['total_playtime'] += run_time
    new_medals = check_new_medals(meta)
    try:
        import cards as C
        new_cards = C.check_unlocks(meta)
    except Exception:
        new_cards = []
    save_meta(meta)
    return [m[0] for m in new_medals], new_cards

def on_line_clear(meta, count):
    return None

def update_persistent(meta, game, run_time):
    pass

def update_live_stats(meta, game):
    s = meta['stats']
    s['total_lines'] += game._last_cleared if hasattr(game, '_last_cleared') else 0
    if game.combo > s['max_combo']:
        s['max_combo'] = game.combo

def save_score(score):
    _ensure_dir()
    scores = load_scores()
    scores.append(int(score))
    scores.sort(reverse=True)
    scores = scores[:10]
    with open(SCORES_FILE, 'w') as f:
        json.dump(scores, f)
    return scores

def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []

def today_key():
    return datetime.date.today().isoformat()

def check_streak(meta):
    today = datetime.date.today()
    last = meta.get('last_daily_date', '')
    if last == today.isoformat():
        return False
    yesterday = (today - datetime.timedelta(days=1)).isoformat()
    meta['daily_streak'] = (meta.get('daily_streak', 0) + 1) if last == yesterday else 1
    meta['last_daily_date'] = today.isoformat()
    save_meta(meta)
    return True

def get_daily_quests():
    day = datetime.date.today()
    h = int(hashlib.md5(day.isoformat().encode()).hexdigest(), 16)
    t1 = 15 + (h % 16)
    t2 = 2000 + (h % 6) * 500
    return [
        {'id': 'daily_lines', 'type': 'lines', 'target': t1,
         'desc': locale.t('d_lines', target=t1)},
        {'id': 'daily_score', 'type': 'score', 'target': t2,
         'desc': locale.t('d_score', target=t2)},
        {'id': 'daily_play', 'type': 'time', 'target': 180,
         'desc': locale.t('d_time', target=3)},
    ]

def daily_progress(meta):
    key = today_key()
    meta.setdefault('dailies', {})
    if key not in meta['dailies']:
        meta['dailies'][key] = {'lines': 0, 'score': 0, 'time': 0}
    return meta['dailies'][key]

def update_daily(meta, lines=0, score=0, dt=0.0):
    p = daily_progress(meta)
    p['lines'] += lines
    p['score'] = max(p['score'], score)
    p['time'] += dt
    save_meta(meta)
