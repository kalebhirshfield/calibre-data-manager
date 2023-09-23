import os
import threading
import psycopg2
from dotenv import load_dotenv
import flet as ft
from flet import RoundedRectangleBorder


load_dotenv()
connection = psycopg2.connect(os.getenv("dbURL"))
cursor = connection.cursor()

offset = 0


def main(page: ft.Page):
    def fetchStockLevels(limit):
        global offset
        cursor.execute("SELECT * FROM stocklevels LIMIT %s OFFSET %s", (limit, offset))
        stockLevels = cursor.fetchall()
        columnNames = [desc[0] for desc in cursor.description]
        offset += limit
        return columnNames, stockLevels

    def fetchHistoricalSales(limit):
        global offset
        cursor.execute(
            "SELECT * FROM historicalsales LIMIT %s OFFSET %s", (limit, offset)
        )
        historicalSales = cursor.fetchall()
        columnNames = [desc[0] for desc in cursor.description]
        offset += limit
        return columnNames, historicalSales

    class State:
        i = 0

    s = State()
    sem = threading.Semaphore()

    def addDataToTable(table, fetch_function, limit, rows):
        columnNames, data = fetch_function(limit=limit)
        new_rows = []
        for row in data:
            new_rows.append(
                ft.DataRow(cells=[ft.DataCell(ft.Text(cell)) for cell in row])
            )
        rows += new_rows
        table.rows = rows
        page.update()

    def onScroll(e: ft.OnScrollEvent):
        if e.pixels >= e.max_scroll_extent - 300:
            if sem.acquire(blocking=False):
                try:
                    addDataToTable(
                        stockLevelsTable, fetchStockLevels, 10, stockLevelsTable.rows
                    )
                    addDataToTable(
                        historicalSalesTable,
                        fetchHistoricalSales,
                        10,
                        historicalSalesTable.rows,
                    )
                finally:
                    sem.release()

    page.title = "Calibre Data Manager"
    page.window_width = 750
    page.window_height = 500
    page.window_title_bar_hidden = True
    page.window_title_bar_buttons_hidden = True
    page.window_min_width = 330
    page.window_min_height = 230

    windowDragArea = ft.WindowDragArea(
        ft.Container(
            ft.Text(
                "Calibre Data Manager",
                color=ft.colors.WHITE70,
                text_align="center",
            ),
            bgcolor=ft.colors.BLACK54,
            padding=10,
            border_radius=10,
        ),
        expand=True,
    )
    btnClose = ft.IconButton(
        ft.icons.CLOSE,
        style=ft.ButtonStyle(
            color={
                ft.MaterialState.DEFAULT: ft.colors.WHITE70,
                ft.MaterialState.HOVERED: ft.colors.RED_ACCENT,
            },
            bgcolor={ft.MaterialState.DEFAULT: ft.colors.BLACK54},
            shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=10)},
        ),
        on_click=lambda _: page.window_close(),
    )

    searchBar = ft.TextField(
        label="Search",
        expand=True,
        border_radius=10,
        prefix_icon=ft.icons.SEARCH,
        # on_change=search,
        text_style=ft.TextStyle(color=ft.colors.WHITE70),
        label_style=ft.TextStyle(color=ft.colors.WHITE70),
        border_width=2,
        focused_border_width=4,
        border_color=ft.colors.BACKGROUND,
        focused_border_color=ft.colors.WHITE70,
        bgcolor=ft.colors.BLACK54,
        focused_bgcolor=ft.colors.BACKGROUND,
        cursor_color=ft.colors.WHITE70,
    )

    stockLevelsTable = ft.DataTable(
        columns=[],
        bgcolor=ft.colors.BLACK54,
        border_radius=10,
    )

    historicalSalesTable = ft.DataTable(
        columns=[],
        bgcolor=ft.colors.BLACK54,
        border_radius=10,
    )

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        divider_color=ft.colors.WHITE70,
        indicator_color=ft.colors.BLUE_ACCENT,
        label_color=ft.colors.WHITE70,
        overlay_color=ft.colors.WHITE10,
        tabs=[
            ft.Tab(
                text="Stock Levels",
                icon=ft.icons.TABLE_ROWS,
                content=ft.Column(
                    [stockLevelsTable], scroll=True, expand=True, on_scroll=onScroll
                ),
            ),
            ft.Tab(
                text="Hisorical Sales",
                icon=ft.icons.TABLE_CHART,
                content=ft.Column(
                    [historicalSalesTable], scroll=True, expand=True, on_scroll=onScroll
                ),
            ),
            ft.Tab(text="Edit Tables", icon=ft.icons.EDIT),
        ],
        expand=True,
    )

    addDataToTable(stockLevelsTable, fetchStockLevels, 10, stockLevelsTable.rows)
    s.i += 10
    addDataToTable(
        historicalSalesTable, fetchHistoricalSales, 10, historicalSalesTable.rows
    )

    stockLevelsColumns, _ = fetchStockLevels(1)
    historicalSalesColumns, _ = fetchHistoricalSales(1)

    stockLevelsTable.columns = [
        ft.DataColumn(ft.Text(column)) for column in stockLevelsColumns
    ]
    historicalSalesTable.columns = [
        ft.DataColumn(ft.Text(column)) for column in historicalSalesColumns
    ]

    page.add(ft.Row([windowDragArea, btnClose]), ft.Row([searchBar]), tabs)


ft.app(target=main)

cursor.close()
connection.close()
