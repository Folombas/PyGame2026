import datetime

SEASON_EPOCH = datetime.date(2025, 1, 1)
SEASON_LENGTH = 30

SEASONS = [
    {'id': 0, 'name_key': 'season_spring', 'color': (120, 220, 120), 'packs': 5},
    {'id': 1, 'name_key': 'season_summer', 'color': (255, 200, 50),  'packs': 5},
    {'id': 2, 'name_key': 'season_autumn', 'color': (220, 120, 50),  'packs': 5},
    {'id': 3, 'name_key': 'season_winter', 'color': (100, 180, 255), 'packs': 5},
]

def get_season_info():
    today = datetime.date.today()
    delta = (today - SEASON_EPOCH).days
    idx = delta // SEASON_LENGTH
    pos = delta % SEASON_LENGTH
    season = SEASONS[idx % len(SEASONS)]
    return {
        'id': idx,
        'season': season,
        'day': pos + 1,
        'days_left': SEASON_LENGTH - pos - 1,
    }

def check_season_reward(meta):
    info = get_season_info()
    last = meta.get('last_season_id', -1)
    if info['id'] > last:
        meta['last_season_id'] = info['id']
        meta['unopened_packs'] = meta.get('unopened_packs', 0) + info['season']['packs']
        try:
            from meta import save_meta
            save_meta(meta)
        except Exception:
            pass
        return True, info['season']['packs']
    return False, 0
