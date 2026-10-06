"""Каталог реальных интернет-радиостанций.

Все потоки — открытые и легальные, предоставлены SomaFM и другими
независимыми радиостанциями. Поддерживаются напрямую через VLC.
"""

# SomaFM — независимое радио из Сан-Франциско (MP3 128kbps)
# Формат: (частота_MHz, название, URL, громкость_множитель)
STATIONS_FM = [
    (88.5, "Groove Salad",   "https://ice1.somafm.com/groovesalad-128-mp3",   1.0),
    (92.0, "Drone Zone",     "https://ice1.somafm.com/dronezone-128-mp3",     0.9),
    (95.5, "Lush",           "https://ice1.somafm.com/lush-128-mp3",          0.9),
    (99.1, "Indie Pop Rocks","https://ice1.somafm.com/indiepop-128-mp3",      1.0),
    (101.7,"Deep Space One", "https://ice1.somafm.com/deepspaceone-128-mp3",  0.9),
    (105.3,"Secret Agent",   "https://ice1.somafm.com/secretagent-128-mp3",   1.0),
]

# Дополнительные потоки (можно использовать в других диапазонах)
STATIONS_SHORTWAVE = [
    (6.5,  "Radio Paradise","https://stream.radioparadise.com/mp3-128",       1.0),
    (11.2, "Classic FM",    "https://media-ssl.musicradio.com/ClassicFMMP3",  0.9),
]

# Объединённая карта диапазонов
ALL_STATIONS = {
    "FM": STATIONS_FM,
    "SW": STATIONS_SHORTWAVE,
}
