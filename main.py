import os
import threading
import psycopg2
from dotenv import load_dotenv
import flet as ft
from flet import RoundedRectangleBorder
import matplotlib
import matplotlib.pyplot as plt
from flet.matplotlib_chart import MatplotlibChart

matplotlib.use("svg")


load_dotenv()
connection = psycopg2.connect(os.getenv("dbURL"))
cursor = connection.cursor()

offset = 0


def main(page: ft.Page):
    def fetchStockLevels(limit):
        global offset
        cursor.execute(
            "SELECT * FROM products d INNER JOIN stocklevels using(stock_code) INNER JOIN stockbalance using(stock_id) LIMIT %s OFFSET %s",
            (limit, offset),
        )
        stockLevels = cursor.fetchall()
        columnNames = [desc[0] for desc in cursor.description]
        offset += limit
        return columnNames, stockLevels

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
                    addDataToTable(
                        stockLevelsTable,
                        fetchStockLevels,
                        10,
                        stockLevelsTable.rows,
                    )

                finally:
                    sem.release()

    def tabSwitch(e):
        searchBar.visible = (
            True if tabs.selected_index == 0 or tabs.selected_index == 1 else False
        )
        searchBar.label = (
            "Enter Stock Code to Display" if tabs.selected_index == 1 else "Search"
        )
        page.update()

    def search(e):
        if tabs.selected_index == 0:
            query = str(searchBar.value.strip())
            if query != "":
                searchStockLevelsTable.visible = True
                stockLevelsTable.visible = False
                columnsToSearch = [column for column in stockLevelsColumns]
                conditions = [
                    f"CAST({column} as TEXT) LIKE %s" for column in columnsToSearch
                ]
                whereClause = " OR ".join(conditions)
                table = "products d INNER JOIN stocklevels using(stock_code) INNER JOIN stockbalance using(stock_id)"
                sqlQuery = f"SELECT * FROM {table} WHERE {whereClause}"
                params = [f"%{query}%"] * len(columnsToSearch)
                cursor.execute(sqlQuery, params)
                searchData = cursor.fetchall()
                rows = []
                for row in searchData:
                    rows.append(
                        ft.DataRow(
                            cells=[ft.DataCell(ft.Text(str(cell))) for cell in row]
                        )
                    )
                    searchStockLevelsTable.rows = rows
                page.update()
            else:
                searchStockLevelsTable.rows = []
                searchStockLevelsTable.visible = False
                stockLevelsTable.visible = True
                page.update()
        elif tabs.selected_index == 1:
            if searchBar.value != "":
                stockCode = str(searchBar.value.strip().upper())
                fig, ax = plt.subplots()
                ax.set_xlabel("Years")
                ax.set_ylabel("Sales")
                ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))
                ax.set_title("Sales by Year")
                ax.grid(True)
                ax.set_facecolor("#1b2628")
                ax.tick_params(axis="x", colors="#e1e3e3")
                ax.tick_params(axis="y", colors="#e1e3e3")
                ax.spines["bottom"].set_color("#e1e3e3")
                ax.spines["top"].set_color("#e1e3e3")
                ax.spines["left"].set_color("#e1e3e3")
                ax.spines["right"].set_color("#e1e3e3")
                ax.xaxis.label.set_color("#e1e3e3")
                ax.yaxis.label.set_color("#e1e3e3")
                ax.title.set_color("#e1e3e3")
                chart = MatplotlibChart(fig, expand=True, transparent=True)
                tabs.tabs[2].content = ft.Container(chart, expand=True)
                page.update()

    sem = threading.Semaphore()

    page.title = "Calibre Data Manager"
    page.window_width = 1200
    page.window_height = 600
    page.window_title_bar_hidden = True
    page.window_title_bar_buttons_hidden = True
    page.window_resizable = True
    page.window_maximizable = False
    page.bgcolor = "#191c1d"

    windowDragArea = ft.WindowDragArea(
        ft.Container(
            ft.Text(
                "Calibre Data Manager",
                color="#e1e3e3",
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
                ft.MaterialState.DEFAULT: "#e1e3e3",
                ft.MaterialState.HOVERED: "#ba1a1a",
            },
            shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=10)},
        ),
        on_click=lambda _: page.window_close(),
    )

    searchBar = ft.TextField(
        label="Search",
        expand=True,
        border_radius=10,
        prefix_icon=ft.icons.SEARCH,
        text_style=ft.TextStyle(color="#e1e3e3"),
        label_style=ft.TextStyle(color="#e1e3e3", weight=ft.FontWeight.BOLD),
        border_width=2,
        focused_border_width=4,
        border_color=ft.colors.TRANSPARENT,
        focused_border_color="#004f58",
        bgcolor=ft.colors.TRANSPARENT,
        focused_bgcolor=ft.colors.TRANSPARENT,
        cursor_color="#e1e3e3",
        on_change=search,
    )

    stockLevelsTable = ft.DataTable(
        bgcolor="#1b2628",
        border_radius=10,
        divider_thickness=0,
        heading_row_height=75,
        horizontal_lines=ft.border.BorderSide(0, "#004f58"),
        heading_text_style=ft.TextStyle(color="#e1e3e3", weight=ft.FontWeight.BOLD),
        data_text_style=ft.TextStyle(color="#e1e3e3"),
    )

    addDataToTable(stockLevelsTable, fetchStockLevels, 10, stockLevelsTable.rows)

    stockLevelsColumns, _ = fetchStockLevels(1)

    stockLevelsTable.columns = [
        ft.DataColumn(ft.Text(column)) for column in stockLevelsColumns
    ]

    searchStockLevelsTable = ft.DataTable(
        columns=[ft.DataColumn(ft.Text(column)) for column in stockLevelsColumns],
        bgcolor="#1b2628",
        border_radius=10,
        divider_thickness=0,
        heading_row_height=75,
        horizontal_lines=ft.border.BorderSide(0, "#004f58"),
        heading_text_style=ft.TextStyle(color="#e1e3e3", weight=ft.FontWeight.BOLD),
        data_text_style=ft.TextStyle(color="#e1e3e3"),
        visible=False,
    )

    stockCodeTF = ft.TextField(
        label="Enter Stock Code",
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#e1e3e3"),
        label_style=ft.TextStyle(color="#e1e3e3"),
        border_width=2,
        focused_border_width=4,
        border_color="#004f58",
        focused_border_color="#d6ca00",
        bgcolor=ft.colors.TRANSPARENT,
        focused_bgcolor=ft.colors.TRANSPARENT,
        cursor_color="#e1e3e3",
    )

    stockCATTF = ft.TextField(
        label="Enter Stock CAT",
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#e1e3e3"),
        label_style=ft.TextStyle(color="#e1e3e3"),
        border_width=2,
        focused_border_width=4,
        border_color="#004f58",
        focused_border_color="#d6ca00",
        bgcolor=ft.colors.TRANSPARENT,
        focused_bgcolor=ft.colors.TRANSPARENT,
        cursor_color="#e1e3e3",
    )

    descriptionTF = ft.TextField(
        label="Enter Description",
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#e1e3e3"),
        label_style=ft.TextStyle(color="#e1e3e3"),
        border_width=2,
        focused_border_width=4,
        border_color="#004f58",
        focused_border_color="#d6ca00",
        bgcolor=ft.colors.TRANSPARENT,
        focused_bgcolor=ft.colors.TRANSPARENT,
        cursor_color="#e1e3e3",
    )

    moqTF = ft.TextField(
        label="Enter Minimum Order Quantity",
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#e1e3e3"),
        label_style=ft.TextStyle(color="#e1e3e3"),
        border_width=2,
        focused_border_width=4,
        border_color="#004f58",
        focused_border_color="#d6ca00",
        bgcolor=ft.colors.TRANSPARENT,
        focused_bgcolor=ft.colors.TRANSPARENT,
        cursor_color="#e1e3e3",
    )

    quantityTF = ft.TextField(
        label="Enter Quantity",
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#e1e3e3"),
        label_style=ft.TextStyle(color="#e1e3e3"),
        border_width=2,
        focused_border_width=4,
        border_color="#004f58",
        focused_border_color="#d6ca00",
        bgcolor=ft.colors.TRANSPARENT,
        focused_bgcolor=ft.colors.TRANSPARENT,
        cursor_color="#e1e3e3",
    )

    addButton = ft.IconButton(
        icon=ft.icons.ADD,
        style=ft.ButtonStyle(
            color={
                ft.MaterialState.DEFAULT: "#e1e3e3",
                ft.MaterialState.HOVERED: "#d6ca00",
            },
            shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=10)},
        ),
    )

    addDataTab = ft.Column(
        [
            ft.Row([stockCodeTF, addButton]),
            ft.Row([stockCATTF]),
            ft.Row([descriptionTF]),
            ft.Row([moqTF]),
        ]
    )

    saleTab = ft.Column(
        [
            ft.Row([stockCodeTF, addButton]),
            ft.Row([quantityTF]),
        ]
    )

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        divider_color=ft.colors.TRANSPARENT,
        indicator_color="#d6ca00",
        label_color="#e1e3e3",
        overlay_color=ft.colors.WHITE10,
        unselected_label_color="#e1e3e3",
        indicator_border_radius=10,
        tabs=[
            ft.Tab(
                text="Browse",
                icon=ft.icons.TABLE_ROWS_ROUNDED,
                content=ft.Column(
                    [stockLevelsTable, searchStockLevelsTable],
                    scroll=True,
                    expand=True,
                    on_scroll=onScroll,
                ),
            ),
            ft.Tab(text="View Sales Patterns", icon=ft.icons.LINE_AXIS_ROUNDED),
            ft.Tab(
                text="Add / Edit Product Data",
                icon=ft.icons.EDIT_ROUNDED,
                content=ft.Container(addDataTab),
            ),
            ft.Tab(
                text="Make A Sale",
                icon=ft.icons.ADD_SHOPPING_CART_ROUNDED,
                content=ft.Container(saleTab),
            ),
        ],
        expand=True,
        on_change=tabSwitch,
    )

    bar = ft.Column(
        [
            ft.Row([windowDragArea, btnClose]),
            ft.Row([searchBar]),
        ]
    )

    titleBar = ft.Row(
        [
            ft.Container(
                bar,
                bgcolor="#1b2628",
                expand=True,
                border_radius=10,
            )
        ]
    )

    page.add(titleBar, tabs)


ft.app(target=main)

cursor.close()
connection.close()
