import json, os, hashlib, datetime
import i18n as locale
from settings import SCORES_FILE, META_FILE

# 5-tier thresholds: wood, bronze, silver, gold, platinum
ACHIEVEMENTS = [
    {'id': 'first_clear', 'name_key': 'ach1', 'desc_key': 'achd1',
     'stat': 'total_lines', 'cat': 'progress', 'points': 10, 'hidden': False,
     'tiers': [1, 50, 200, 500, 1000]},
    {'id': 'tetris', 'name_key': 'ach2', 'desc_key': 'achd2',
     'stat': 'tetris_count', 'cat': 'skill', 'points': 25, 'hidden': False,
     'tiers': [1, 5, 20, 50, 100]},
    {'id': 'combo3', 'name_key': 'ach3', 'desc_key': 'achd3',
     'stat': 'max_combo', 'cat': 'skill', 'points': 15, 'hidden': False,
     'tiers': [2, 4, 7, 10, 15]},
    {'id': 'combo5', 'name_key': 'ach4', 'desc_key': 'achd4',
     'stat': 'max_combo', 'cat': 'skill', 'points': 30, 'hidden': False,
     'tiers': [4, 7, 10, 15, 20]},
    {'id': 'level5', 'name_key': 'ach5', 'desc_key': 'achd5',
     'stat': 'best_level', 'cat': 'progress', 'points': 20, 'hidden': False,
     'tiers': [5, 8, 12, 15, 20]},
    {'id': 'level10', 'name_key': 'ach6', 'desc_key': 'achd6',
     'stat': 'best_level', 'cat': 'progress', 'points': 40, 'hidden': False,
     'tiers': [10, 13, 16, 20, 25]},
    {'id': 'score5k', 'name_key': 'ach7', 'desc_key': 'achd7',
     'stat': 'best_score', 'cat': 'progress', 'points': 20, 'hidden': False,
     'tiers': [5000, 15000, 30000, 50000, 100000]},
    {'id': 'score20k', 'name_key': 'ach8', 'desc_key': 'achd8',
     'stat': 'best_score', 'cat': 'progress', 'points': 40, 'hidden': False,
     'tiers': [20000, 40000, 75000, 150000, 300000]},
    {'id': 'marathon', 'name_key': 'ach9', 'desc_key': 'achd9',
     'stat': 'longest_run', 'cat': 'endurance', 'points': 30, 'hidden': False,
     'tiers': [60, 180, 300, 600, 1200]},
    {'id': 'lines50', 'name_key': 'ach10', 'desc_key': 'achd10',
     'stat': 'total_lines', 'cat': 'progress', 'points': 25, 'hidden': False,
     'tiers': [50, 250, 500, 1000, 2000]},
    # NEW achievements
    {'id': 'b2b', 'name_key': 'ach11', 'desc_key': 'achd11',
     'stat': 'b2b_count', 'cat': 'skill', 'points': 30, 'hidden': False,
     'tiers': [1, 5, 15, 30, 60]},
    {'id': 'perfect_clear', 'name_key': 'ach12', 'desc_key': 'achd12',
     'stat': 'perfect_clears', 'cat': 'mastery', 'points': 50, 'hidden': False,
     'tiers': [1, 3, 10, 25, 50]},
    {'id': 'hold_master', 'name_key': 'ach13', 'desc_key': 'achd13',
     'stat': 'hold_uses', 'cat': 'progress', 'points': 15, 'hidden': False,
     'tiers': [10, 50, 150, 400, 1000]},
    {'id': 'sprint_win', 'name_key': 'ach14', 'desc_key': 'achd14',
     'stat': 'sprint_wins', 'cat': 'skill', 'points': 35, 'hidden': False,
     'tiers': [1, 5, 15, 30, 60]},
    {'id': 'secret_zen', 'name_key': 'ach15', 'desc_key': 'achd15',
     'stat': 'zen_games', 'cat': 'mastery', 'points': 15, 'hidden': True,
     'tiers': [5, 15, 40, 100, 250]},
]

def _default_stats():
    return {
        'total_lines': 0, 'best_score': 0, 'best_level': 1,
        'max_combo': 0, 'tetris_count': 0, 'longest_run': 0,
        'b2b_count': 0, 'perfect_clears': 0, 'hold_uses': 0,
        'sprint_wins': 0, 'zen_games': 0,
    }

def _default_meta():
    return {
        'lang': 'en',
        'stats': _default_stats(),
        'unlocked': {}, 'medals': {}, 'cards': {}, 'card_dups': {},
        'player_level': 1, 'xp': 0, 'xp_needed': 100,
        'best_sprint_time': 999999.0, 'dailies': {}, 'weeklies': {},
        'daily_streak': 0, 'last_daily_date': '',
        'best_score': 0, 'total_lines': 0, 'total_playtime': 0.0,
        'unopened_packs': 0, 'best_weekly_iso': '',
        'completed_sets': [], 'last_season_id': -1,
        'foil_cards': {}, 'streak_skip_tokens': 0,
        'last_played_date': '',
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
                elif k in ('dailies', 'weeklies') and isinstance(v, dict):
                    base[k].update(v)
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
    tier = 0
    for i, th in enumerate(ach['tiers']):
        if val >= th:
            tier = i + 1
    return tier

def get_progress(meta, ach):
    val = meta['stats'].get(ach['stat'], 0)
    tier = get_medal_tier(meta, ach)
    if tier >= 5:
        return val, ach['tiers'][4], 5
    return val, ach['tiers'][tier], tier

def get_achievement_points(meta):
    total = 0
    for a in ACHIEVEMENTS:
        t = meta['medals'].get(a['id'], 0)
        total += a['points'] * t
    return total

def get_global_rank(meta):
    ap = get_achievement_points(meta)
    if ap >= 5000: return 10
    if ap >= 3000: return 9
    if ap >= 2000: return 8
    if ap >= 1500: return 7
    if ap >= 1000: return 6
    if ap >= 600: return 5
    if ap >= 300: return 4
    if ap >= 150: return 3
    if ap >= 50: return 2
    if ap >= 10: return 1
    return 0

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
    if getattr(game, 'b2b_count', 0) > 0:
        s['b2b_count'] = max(s['b2b_count'], getattr(game, 'b2b_count', 0))
    if getattr(game, 'hold_uses', 0) > 0:
        s['hold_uses'] += getattr(game, 'hold_uses', 0)
    if getattr(game, 'zen', False):
        s['zen_games'] += 1
    if getattr(game, 'win', False) and game.mode == 'sprint':
        s['sprint_wins'] += 1
    meta['best_score'] = s['best_score']
    meta['total_lines'] = s['total_lines']
    meta['total_playtime'] += run_time
    new_medals = check_new_medals(meta)
    try:
        import cards as C
        new_cards = C.check_unlocks(meta)
        new_sets = C.check_completed_sets(meta)
    except Exception:
        new_cards = []
        new_sets = []
    # Reward for new medals: +1 pack per medal
    meta['unopened_packs'] = meta.get('unopened_packs', 0) + len(new_medals)
    save_meta(meta)
    if new_sets:
        meta['_new_sets'] = new_sets
    return [m[0] for m in new_medals], new_cards

def on_line_clear(meta, count):
    return None

def update_persistent(meta, game, run_time):
    pass

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

def week_key():
    d = datetime.date.today()
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"

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

def get_streak_multiplier(meta):
    return min(7, max(1, meta.get('daily_streak', 1)))

def get_daily_quests():
    day = datetime.date.today()
    h = int(hashlib.md5(day.isoformat().encode()).hexdigest(), 16)
    t1 = 15 + (h % 16)
    t2 = 2000 + (h % 6) * 500
    return [
        {'id': 'daily_lines', 'type': 'lines', 'target': t1,
         'desc': locale.t('d_lines', target=t1), 'reward_xp': 20, 'reward_packs': 0},
        {'id': 'daily_score', 'type': 'score', 'target': t2,
         'desc': locale.t('d_score', target=t2), 'reward_xp': 30, 'reward_packs': 0},
        {'id': 'daily_play', 'type': 'time', 'target': 180,
         'desc': locale.t('d_time', target=3), 'reward_xp': 25, 'reward_packs': 1},
    ]

def get_weekly_quests():
    h = int(hashlib.md5(week_key().encode()).hexdigest(), 16)
    t1 = 100 + (h % 50)
    return [
        {'id': 'weekly_lines', 'type': 'lines', 'target': t1,
         'desc': locale.t('w_lines', target=t1), 'reward_xp': 150, 'reward_packs': 2},
        {'id': 'weekly_score', 'type': 'score', 'target': 15000 + (h % 5) * 5000,
         'desc': locale.t('w_score', target=15000 + (h % 5) * 5000), 'reward_xp': 200, 'reward_packs': 3},
    ]

def daily_progress(meta):
    key = today_key()
    meta.setdefault('dailies', {})
    if key not in meta['dailies']:
        meta['dailies'][key] = {'lines': 0, 'score': 0, 'time': 0, 'done': []}
    return meta['dailies'][key]

def weekly_progress(meta):
    key = week_key()
    meta.setdefault('weeklies', {})
    if key not in meta['weeklies']:
        meta['weeklies'][key] = {'lines': 0, 'score': 0, 'done': []}
    return meta['weeklies'][key]

def update_daily(meta, lines=0, score=0, dt=0.0):
    p = daily_progress(meta)
    p['lines'] += lines
    p['score'] = max(p['score'], score)
    p['time'] += dt
    w = weekly_progress(meta)
    w['lines'] += lines
    w['score'] = max(w['score'], score)
    save_meta(meta)

def claim_quest_reward(meta, quest_type, period='daily'):
    if period == 'daily':
        prog = daily_progress(meta)
        quests = get_daily_quests()
    else:
        prog = weekly_progress(meta)
        quests = get_weekly_quests()
    for q in quests:
        if q['type'] == quest_type:
            cur = prog.get(q['type'], 0)
            if cur >= q['target'] and q['id'] not in prog['done']:
                prog['done'].append(q['id'])
                meta['xp'] = meta.get('xp', 0) + q['reward_xp']
                meta['unopened_packs'] = meta.get('unopened_packs', 0) + q['reward_packs']
                save_meta(meta)
                return q
    return None
