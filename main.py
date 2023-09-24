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

    sem = threading.Semaphore()

    def addDataToTable(table, fetchFunction, limit, rows):
        columnNames, data = fetchFunction(limit=limit)
        newRows = []
        for row in data:
            newRows.append(
                ft.DataRow(cells=[ft.DataCell(ft.Text(cell)) for cell in row])
            )
        rows += newRows
        table.rows = rows
        page.update()

    def onScroll(e: ft.OnScrollEvent):
        if e.pixels >= e.max_scroll_extent - 300:
            if sem.acquire(blocking=False):
                try:
                    if tabs.selected_index == 0:
                        addDataToTable(
                            stockLevelsTable,
                            fetchStockLevels,
                            10,
                            stockLevelsTable.rows,
                        )
                    elif tabs.selected_index == 1:
                        addDataToTable(
                            historicalSalesTable,
                            fetchHistoricalSales,
                            10,
                            historicalSalesTable.rows,
                        )
                finally:
                    sem.release()

    def search(e):
        query = str(searchBar.value.strip())
        if query != "":
            columnsToSearch = (
                [column for column in stockLevelsColumns]
                if tabs.selected_index == 2
                else [column for column in historicalSalesColumns]
            )
            conditions = [
                f"CAST({column} as TEXT) LIKE %s" for column in columnsToSearch
            ]
            whereClause = " OR ".join(conditions)
            table = "stocklevels" if tabs.selected_index == 2 else "historicalsales"
            sqlQuery = f"SELECT * FROM {table} WHERE {whereClause}"
            params = [f"%{query}%"] * len(columnsToSearch)
            cursor.execute(sqlQuery, params)
            searchData = cursor.fetchall()
            rows = []
            for row in searchData:
                rows.append(
                    ft.DataRow(cells=[ft.DataCell(ft.Text(str(cell))) for cell in row])
                )
            if tabs.selected_index == 2:
                searchStockLevelsTable.rows = rows
            elif tabs.selected_index == 3:
                searchHistoricalSalesTable.rows = rows
            page.update()
        else:
            if tabs.selected_index == 2:
                searchStockLevelsTable.rows = []
            elif tabs.selected_index == 3:
                searchHistoricalSalesTable.rows = []
            page.update()

    page.title = "Calibre Data Manager"
    page.window_width = 1000
    page.window_height = 700
    page.window_title_bar_hidden = True
    page.window_title_bar_buttons_hidden = True
    page.window_resizable = False
    page.window_maximizable = False

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
        maximizable=False,
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
        on_change=search,
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
        bgcolor=ft.colors.BLACK54,
        border_radius=10,
    )

    historicalSalesTable = ft.DataTable(
        bgcolor=ft.colors.BLACK54,
        border_radius=10,
    )

    addDataToTable(stockLevelsTable, fetchStockLevels, 10, stockLevelsTable.rows)
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

    searchStockLevelsTable = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("stock_cat")),
            ft.DataColumn(ft.Text("stock_code")),
            ft.DataColumn(ft.Text("description")),
            ft.DataColumn(ft.Text("quantity")),
            ft.DataColumn(ft.Text("moq")),
            ft.DataColumn(ft.Text("on_order")),
            ft.DataColumn(ft.Text("balance")),
        ],
        bgcolor=ft.colors.BLACK54,
        border_radius=10,
    )

    searchHistoricalSalesTable = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("stock_cat")),
            ft.DataColumn(ft.Text("stock_code")),
            ft.DataColumn(ft.Text("description")),
            ft.DataColumn(ft.Text("2022")),
            ft.DataColumn(ft.Text("2021")),
            ft.DataColumn(ft.Text("2020")),
            ft.DataColumn(ft.Text("2019")),
            ft.DataColumn(ft.Text("2018")),
        ],
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
            ft.Tab(
                text="Search Stock Levels",
                icon=ft.icons.SEARCH,
                content=ft.Column([searchStockLevelsTable], scroll=True, expand=True),
            ),
            ft.Tab(
                text="Search Historical Sales",
                icon=ft.icons.SEARCH,
                content=ft.Column(
                    [searchHistoricalSalesTable], scroll=True, expand=True
                ),
            ),
        ],
        expand=True,
        on_change=search,
    )

    page.add(ft.Row([windowDragArea, btnClose]), ft.Row([searchBar]), tabs)


ft.app(target=main)

cursor.close()
connection.close()
