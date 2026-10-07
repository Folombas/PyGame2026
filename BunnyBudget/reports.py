"""Отчёты и красивый вывод через rich."""
from datetime import datetime
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress


console = Console()


def fmt_money(n):
    """Формат: 12 345.67 ₽"""
    return f"{n:,.2f} ₽".replace(",", " ")


def show_transactions(transactions):
    if not transactions:
        console.print("[yellow]Транзакций нет[/yellow]")
        return
    table = Table(title="Последние транзакции", show_lines=False)
    table.add_column("ID", style="dim", width=5)
    table.add_column("Дата", style="cyan", width=12)
    table.add_column("Сумма", justify="right", width=14)
    table.add_column("Категория", style="magenta", width=14)
    table.add_column("Описание")

    for t in transactions:
        is_spend = t["kind"] == "spend"
        amount = f"[red]-{fmt_money(t['amount'])}[/red]" if is_spend \
            else f"[green]+{fmt_money(t['amount'])}[/green]"
        table.add_row(
            str(t["id"]),
            t["date"],
            amount,
            t["category"],
            t["description"],
        )
    console.print(table)


def month_report(storage, year=None, month=None):
    if year is None or month is None:
        now = datetime.now()
        year, month = now.year, now.month

    txns = storage.month(year, month)
    if not txns:
        console.print(f"[yellow]Нет данных за {year:04d}-{month:02d}[/yellow]")
        return

    # Считаем
    spend_total = sum(t["amount"] for t in txns if t["kind"] == "spend")
    earn_total = sum(t["amount"] for t in txns if t["kind"] == "earn")
    balance = earn_total - spend_total

    # По категориям (расход)
    by_cat = defaultdict(float)
    for t in txns:
        if t["kind"] == "spend":
            by_cat[t["category"]] += t["amount"]

    # Заголовок
    console.print()
    title = f"[bold]Отчёт за {year:04d}-{month:02d}[/bold]"
    console.print(Panel(title, expand=False))
    console.print()

    # Итоги
    console.print(f"  💰 Всего доходов:   [green]{fmt_money(earn_total)}[/green]")
    console.print(f"  💸 Всего расходов:  [red]{fmt_money(spend_total)}[/red]")
    if balance >= 0:
        console.print(f"  ✅ Баланс:          [green]{fmt_money(balance)}[/green]")
    else:
        console.print(f"  ⚠️  Баланс:          [red]{fmt_money(balance)}[/red]")
    console.print()

    # Таблица по категориям
    if by_cat:
        table = Table(title="Расходы по категориям")
        table.add_column("Категория", style="magenta")
        table.add_column("Сумма", justify="right")
        table.add_column("% от расходов", justify="right")
        table.add_column("Бары", width=20)

        total_spend = sum(by_cat.values())
        for cat, s in sorted(by_cat.items(), key=lambda x: -x[1]):
            pct = s / total_spend * 100
            bar_len = int(pct / 5)
            bar = "█" * bar_len
            table.add_row(
                cat,
                fmt_money(s),
                f"{pct:.1f}%",
                f"[red]{bar}[/red]",
            )
        console.print(table)


def all_months_summary(storage):
    """Краткая сводка по всем месяцам."""
    months = storage.months()
    if not months:
        console.print("[yellow]Данных пока нет[/yellow]")
        return

    table = Table(title="История по месяцам")
    table.add_column("Месяц")
    table.add_column("Доходы", justify="right")
    table.add_column("Расходы", justify="right")
    table.add_column("Баланс", justify="right")

    for m in months:
        year, month = map(int, m.split("-"))
        txns = storage.month(year, month)
        earn = sum(t["amount"] for t in txns if t["kind"] == "earn")
        spend = sum(t["amount"] for t in txns if t["kind"] == "spend")
        bal = earn - spend
        sign = "[green]" if bal >= 0 else "[red]"
        table.add_row(
            m,
            f"[green]{fmt_money(earn)}[/green]",
            f"[red]{fmt_money(spend)}[/red]",
            f"{sign}{fmt_money(bal)}[/]" if False else f"[{'green' if bal>=0 else 'red'}]{fmt_money(bal)}[/]",
        )
    console.print(table)
