"""BunnyBudget — учёт расходов и доходов."""
import argparse
import sys
from datetime import datetime

from rich.console import Console
from storage import Storage
from categories import categorize, all_categories
from reports import show_transactions, month_report, all_months_summary, fmt_money


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

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
