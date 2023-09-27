import os
import threading
import psycopg2
from dotenv import load_dotenv
import flet as ft
from flet import RoundedRectangleBorder


load_dotenv()
connection = psycopg2.connect(os.getenv("dbURL"))
cursor = connection.cursor()

offsetStock = 0
offsetSales = 0


def main(page: ft.Page):
    def fetchStockLevels(limit):
        global offsetStock
        cursor.execute(
            "SELECT * FROM stocklevels LIMIT %s OFFSET %s", (limit, offsetStock)
        )
        stockLevels = cursor.fetchall()
        columnNames = [desc[0] for desc in cursor.description]
        offsetStock += limit
        return columnNames, stockLevels

    def fetchHistoricalSales(limit):
        global offsetSales
        cursor.execute(
            "SELECT * FROM historicalsales LIMIT %s OFFSET %s", (limit, offsetSales)
        )
        historicalSales = cursor.fetchall()
        columnNames = [desc[0] for desc in cursor.description]
        offsetSales += limit
        return columnNames, historicalSales

    sem = threading.Semaphore()

    def addDataToTable(table: ft.DataTable, fetchFunction, limit, rows):
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
        if tabs.selected_index == 2 or tabs.selected_index == 3:
            searchBar.visible = True
        else:
            searchBar.visible = False
        query = str(searchBar.value.strip())
        if query != "":
            searchHistoricalSalesTable.visible = True
            searchStockLevelsTable.visible = True
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
            searchHistoricalSalesTable.visible = False
            searchStockLevelsTable.visible = False
            page.update()

    page.title = "Calibre Data Manager"
    page.window_width = 1000
    page.window_height = 600
    page.window_title_bar_hidden = True
    page.window_title_bar_buttons_hidden = True
    page.window_resizable = False
    page.window_maximizable = False
    page.bgcolor = "#001f25"

    windowDragArea = ft.WindowDragArea(
        ft.Container(
            ft.Text(
                "Calibre Data Manager",
                color="#a6eeff",
                text_align="center",
                weight=ft.FontWeight.BOLD,
            ),
            padding=10,
        ),
        expand=True,
        maximizable=False,
    )

    btnClose = ft.IconButton(
        ft.icons.CLOSE,
        style=ft.ButtonStyle(
            color={
                ft.MaterialState.DEFAULT: "#a6eeff",
                ft.MaterialState.HOVERED: "#ffb4ab",
            },
            shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=10)},
        ),
        on_click=lambda _: page.window_close(),
    )

    searchBar = ft.TextField(
        label="Press Enter to Search",
        expand=True,
        border_radius=10,
        prefix_icon=ft.icons.SEARCH,
        text_style=ft.TextStyle(color="#4dd8e6"),
        label_style=ft.TextStyle(color="#a6eeff", weight=ft.FontWeight.BOLD),
        border_width=2,
        focused_border_width=4,
        border_color=ft.colors.TRANSPARENT,
        focused_border_color="#004f55",
        bgcolor=ft.colors.TRANSPARENT,
        focused_bgcolor=ft.colors.TRANSPARENT,
        cursor_color="#a6eeff",
        visible=False,
        on_submit=search,
    )

    stockLevelsTable = ft.DataTable(bgcolor="#04282f", border_radius=10)

    historicalSalesTable = ft.DataTable(bgcolor="#04282f", border_radius=10)

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
        columns=[ft.DataColumn(ft.Text(column)) for column in stockLevelsColumns],
        bgcolor="#04282f",
        border_radius=10,
        visible=False,
    )

    searchHistoricalSalesTable = ft.DataTable(
        columns=[ft.DataColumn(ft.Text(column)) for column in historicalSalesColumns],
        bgcolor="#04282f",
        border_radius=10,
        visible=False,
    )

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        divider_color=ft.colors.TRANSPARENT,
        indicator_color="#d3cb00",
        label_color="#a6eeff",
        overlay_color=ft.colors.WHITE10,
        unselected_label_color="#a6eeff",
        indicator_border_radius=10,
        tabs=[
            ft.Tab(
                text="Browse Stock Levels",
                icon=ft.icons.TABLE_ROWS,
                content=ft.Column(
                    [stockLevelsTable], scroll=True, expand=True, on_scroll=onScroll
                ),
            ),
            ft.Tab(
                text="Browse Hisorical Sales",
                icon=ft.icons.TABLE_CHART,
                content=ft.Column(
                    [historicalSalesTable], scroll=True, expand=True, on_scroll=onScroll
                ),
            ),
            ft.Tab(
                text="Search Stock Levels",
                icon=ft.icons.SEARCH,
                content=ft.Container(
                    ft.Column([searchStockLevelsTable], scroll=True, expand=True),
                ),
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

    bar = ft.Column([ft.Row([windowDragArea, btnClose]), ft.Row([searchBar])])

    titleBar = ft.Row(
        [
            ft.Container(
                bar,
                bgcolor="#04282f",
                expand=True,
                border_radius=10,
            )
        ]
    )

    page.add(titleBar, tabs)


ft.app(target=main)

cursor.close()
connection.close()
