import json, os, hashlib, datetime
import locale
from settings import META_FILE, SCORES_FILE

ACHIEVEMENTS = [
    {'id': 'first_clear', 'name_key': 'ach1',  'desc_key': 'achd1'},
    {'id': 'tetris',      'name_key': 'ach2',  'desc_key': 'achd2'},
    {'id': 'combo3',      'name_key': 'ach3',  'desc_key': 'achd3'},
    {'id': 'combo5',      'name_key': 'ach4',  'desc_key': 'achd4'},
    {'id': 'level5',      'name_key': 'ach5',  'desc_key': 'achd5'},
    {'id': 'level10',     'name_key': 'ach6',  'desc_key': 'achd6'},
    {'id': 'score5k',     'name_key': 'ach7',  'desc_key': 'achd7'},
    {'id': 'score20k',    'name_key': 'ach8',  'desc_key': 'achd8'},
    {'id': 'marathon',    'name_key': 'ach9',  'desc_key': 'achd9'},
    {'id': 'lines50',     'name_key': 'ach10', 'desc_key': 'achd10'},
]

def _default_meta():
    return {'unlocked': {}, 'total_lines': 0, 'best_score': 0,
            'total_playtime': 0.0, 'dailies': {}}

def _ensure_dir():
    os.makedirs(os.path.dirname(META_FILE), exist_ok=True)

def load_meta():
    _ensure_dir()
    if os.path.exists(META_FILE):
        try:
            with open(META_FILE) as f:
                data = json.load(f)
            base = _default_meta()
            base.update(data)
            return base
        except Exception:
            pass
    return _default_meta()

def save_meta(meta):
    _ensure_dir()
    with open(META_FILE, 'w') as f:
        json.dump(meta, f, indent=2)

def unlock(meta, aid):
    if aid in meta['unlocked']:
        return False
    meta['unlocked'][aid] = True
    save_meta(meta)
    return True

def check_run(meta, game, run_time):
    newly = []
    if game.lines > 0          and unlock(meta, 'first_clear'): newly.append('first_clear')
    if game.max_combo >= 2     and unlock(meta, 'combo3'):      newly.append('combo3')
    if game.max_combo >= 4     and unlock(meta, 'combo5'):      newly.append('combo5')
    if game.level >= 5         and unlock(meta, 'level5'):      newly.append('level5')
    if game.level >= 10        and unlock(meta, 'level10'):     newly.append('level10')
    if game.score >= 5000      and unlock(meta, 'score5k'):     newly.append('score5k')
    if game.score >= 20000     and unlock(meta, 'score20k'):    newly.append('score20k')
    if run_time >= 300         and unlock(meta, 'marathon'):    newly.append('marathon')
    return newly

def on_line_clear(meta, count):
    if count == 4 and unlock(meta, 'tetris'):
        return 'tetris'
    return None

def update_persistent(meta, game, run_time):
    meta['total_lines'] += game.lines
    meta['total_playtime'] += run_time
    if game.score > meta['best_score']:
        meta['best_score'] = game.score
    if meta['total_lines'] >= 50 and unlock(meta, 'lines50'):
        pass
    save_meta(meta)

def save_score(score):
    _ensure_dir()
    scores = []
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE) as f:
                scores = json.load(f)
        except Exception:
            scores = []
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
        {'id': 'daily_play',  'type': 'time',  'target': 180,
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
