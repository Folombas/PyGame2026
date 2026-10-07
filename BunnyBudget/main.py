"""BunnyBudget — учёт расходов и доходов."""
import argparse
import sys
from datetime import datetime

from rich.console import Console
from rich.table import Table
from storage import Storage
from categories import categorize, all_categories
from reports import (show_transactions, month_report, all_months_summary,
                     fmt_money, compare_months, search_transactions)
import budgets


console = Console()


def cmd_spend(args):
    st = Storage()
    cat = args.category or categorize(args.description)
    tx_id = st.add(args.amount, args.description, cat, "spend")
    console.print(
        f"[red]💸 Расход[/red] [bold]{fmt_money(args.amount)}[/bold] "
        f"→ [magenta]{cat}[/magenta]  (#{tx_id})"
    )


def cmd_earn(args):
    st = Storage()
    cat = args.category or categorize(args.description)
    tx_id = st.add(args.amount, args.description, cat, "earn")
    console.print(
        f"[green]💰 Доход[/green] [bold]{fmt_money(args.amount)}[/bold] "
        f"→ [magenta]{cat}[/magenta]  (#{tx_id})"
    )


def cmd_list(args):
    st = Storage()
    show_transactions(st.list(args.limit))


def cmd_report(args):
    st = Storage()
    if args.month:
        try:
            year, month = map(int, args.month.split("-"))
        except ValueError:
            console.print("[red]Формат месяца: YYYY-MM (например, 2026-10)[/red]")
            sys.exit(1)
        month_report(st, year, month)
    else:
        month_report(st)


def cmd_history(args):
    st = Storage()
    all_months_summary(st)


def cmd_delete(args):
    st = Storage()
    if st.delete(args.id):
        console.print(f"[green]✓ Удалено #{args.id}[/green]")
    else:
        console.print(f"[red]✗ Не найдено #{args.id}[/red]")


def cmd_cats(args):
    console.print("[bold]Доступные категории:[/bold]")
    for c in all_categories():
        console.print(f"  • {c}")



def cmd_budget(args):
    """Управление лимитами."""
    action = args.action
    if action == "set":
        if not args.category or args.amount is None:
            console.print("[red]Использование: budget set КАТЕГОРИЯ СУММА[/red]")
            return
        budgets.set_limit(args.category, args.amount)
        console.print(f"[green]✓ Лимит {args.category}: {fmt_money(args.amount)}[/green]")
    elif action == "list":
        limits = budgets.all_limits()
        if not limits:
            console.print("[yellow]Лимитов пока нет[/yellow]")
            console.print("Установи: [cyan]budget set Еда 15000[/cyan]")
            return
        table = Table(title="Установленные лимиты")
        table.add_column("Категория", style="magenta")
        table.add_column("Лимит", justify="right")
        for c, v in sorted(limits.items()):
            table.add_row(c, fmt_money(v))
        console.print(table)
    elif action == "delete":
        if not args.category:
            console.print("[red]Укажи категорию[/red]")
            return
        if budgets.delete_limit(args.category):
            console.print(f"[green]✓ Лимит {args.category} удалён[/green]")
        else:
            console.print(f"[red]✗ Лимит для {args.category} не найден[/red]")



def cmd_compare(args):
    """Сравнение с прошлым месяцем."""
    st = Storage()
    if args.month:
        try:
            year, month = map(int, args.month.split("-"))
        except ValueError:
            console.print("[red]Формат: YYYY-MM[/red]")
            return
    else:
        now = datetime.now()
        year, month = now.year, now.month
    compare_months(st, year, month)


def cmd_search(args):
    """Поиск по описанию."""
    st = Storage()
    search_transactions(st, args.query)


def main():
    p = argparse.ArgumentParser(
        prog="budget",
        description="BunnyBudget — учёт расходов и доходов",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # spend
    sp = sub.add_parser("spend", help="Записать расход")
    sp.add_argument("amount", type=float, help="Сумма (руб)")
    sp.add_argument("description", help="Описание")
    sp.add_argument("-c", "--category", help="Категория (иначе авто)")
    sp.set_defaults(func=cmd_spend)

    # earn
    ep = sub.add_parser("earn", help="Записать доход")
    ep.add_argument("amount", type=float)
    ep.add_argument("description")
    ep.add_argument("-c", "--category")
    ep.set_defaults(func=cmd_earn)

    # list
    lp = sub.add_parser("list", help="Последние транзакции")
    lp.add_argument("-n", "--limit", type=int, default=20)
    lp.set_defaults(func=cmd_list)

    # report
    rp = sub.add_parser("report", help="Отчёт за месяц")
    rp.add_argument("month", nargs="?", help="YYYY-MM (по умолчанию — текущий)")
    rp.set_defaults(func=cmd_report)

    # history
    hp = sub.add_parser("history", help="История по всем месяцам")
    hp.set_defaults(func=cmd_history)

    # delete
    dp = sub.add_parser("delete", help="Удалить транзакцию")
    dp.add_argument("id", type=int)
    dp.set_defaults(func=cmd_delete)

    # cats
    cp = sub.add_parser("cats", help="Список категорий")
    cp.set_defaults(func=cmd_cats)

    # compare
    cmp = sub.add_parser("compare", help="Сравнить с прошлым месяцем")
    cmp.add_argument("month", nargs="?", help="YYYY-MM (по умолчанию — текущий)")
    cmp.set_defaults(func=cmd_compare)

    # search
    sr = sub.add_parser("search", help="Поиск по описанию")
    sr.add_argument("query", help="Что искать")
    sr.set_defaults(func=cmd_search)

    # budget
    bp = sub.add_parser("budget", help="Управление лимитами")
    bp.add_argument("action", choices=["set", "list", "delete"],
                    help="set | list | delete")
    bp.add_argument("category", nargs="?", help="Категория")
    bp.add_argument("amount", nargs="?", type=float, help="Лимит в рублях")
    bp.set_defaults(func=cmd_budget)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
