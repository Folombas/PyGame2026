# 🔥 REAL BASH в BunnyOS

Настоящий bash твоего Linux внутри PyGame-окна.

## Установка
sudo apt install bubblewrap

## Запуск
В BunnyOS: терминал -> realbash
Или Меню Пуск -> REAL BASH

## Управление
- ENTER — выполнить
- Ctrl+C — прервать
- Ctrl+D — выход из bash
- Ctrl+L — очистить
- Esc — назад в BunnyOS

## Примеры команд
uname -a
df -h
ls ~/bunny_sandbox
python3 --version

## Безопасность
- bwrap: / read-only, ~/bunny_sandbox read-write
- Blacklist: rm -rf /, mkfs, shutdown и т.д.

## Философия
Фейнман: не играть, а ПОНИМАТЬ машину.
