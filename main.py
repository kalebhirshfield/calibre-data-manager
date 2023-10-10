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
                    if tableBrowseSelection.value == "Stock Levels":
                        addDataToTable(
                            stockLevelsTable,
                            fetchStockLevels,
                            10,
                            stockLevelsTable.rows,
                        )
                    elif tableBrowseSelection.value == "Historical Sales":
                        addDataToTable(
                            historicalSalesTable,
                            fetchHistoricalSales,
                            10,
                            historicalSalesTable.rows,
                        )
                finally:
                    sem.release()

    def tableSwitcher(e):
        stockLevelsTable.visible = (
            True if tableBrowseSelection.value == "Stock Levels" else False
        )
        historicalSalesTable.visible = (
            True if tableBrowseSelection.value == "Historical Sales" else False
        )
        page.update()

    def search(e):
        if tabs.selected_index == 1:
            searchBar.label = "Press Enter to Search"
            searchBar.visible = True
            tableSearchSelection.visible = True
            tableBrowseSelection.visible = False
            page.update()
            query = str(searchBar.value.strip())
            if query != "":
                searchHistoricalSalesTable.visible = (
                    True if tableSearchSelection.value == "Historical Sales" else False
                )
                searchStockLevelsTable.visible = (
                    True if tableSearchSelection.value == "Stock Levels" else False
                )
                columnsToSearch = (
                    [column for column in stockLevelsColumns]
                    if tableSearchSelection.value == "Stock Levels"
                    else [column for column in historicalSalesColumns]
                )
                conditions = [
                    f"CAST({column} as TEXT) LIKE %s" for column in columnsToSearch
                ]
                whereClause = " OR ".join(conditions)
                table = (
                    "stocklevels"
                    if tableSearchSelection.value == "Stock Levels"
                    else "historicalsales"
                )
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
                if tableSearchSelection.value == "Stock Levels":
                    searchStockLevelsTable.rows = rows
                elif tableSearchSelection.value == "Historical Sales":
                    searchHistoricalSalesTable.rows = rows
                page.update()
            else:
                if tableSearchSelection.value == "Stock Levels":
                    searchStockLevelsTable.rows = []
                elif tableSearchSelection.value == "Historical Sales":
                    searchHistoricalSalesTable.rows = []
                searchHistoricalSalesTable.visible = False
                searchStockLevelsTable.visible = False
                page.update()
        elif tabs.selected_index == 0:
            tableBrowseSelection.visible = True
            searchBar.visible = False
            tableSearchSelection.visible = False
            page.update()
        elif tabs.selected_index == 2:
            searchBar.label = "Enter Stock Code to Display"
            searchBar.visible = True
            tableSearchSelection.visible = False
            tableBrowseSelection.visible = False
            page.update()
            if searchBar.value != "":
                stockCode = str(searchBar.value.strip().upper())
                fig, ax = plt.subplots()
                years = [2018, 2019, 2020, 2021, 2022]
                cursor.execute(
                    f"SELECT * FROM historicalsales WHERE stock_code = '{stockCode}'"
                )
                allSales = cursor.fetchone()
                sales2018 = allSales[7]
                sales2019 = allSales[6]
                sales2020 = allSales[5]
                sales2021 = allSales[4]
                sales2022 = allSales[3]
                sales = [sales2018, sales2019, sales2020, sales2021, sales2022]
                ax.plot(years, sales, color="#d6ca00", linewidth=3)
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
            elif tabs.selected_index == 3:
                searchBar.visible = False
                tableSearchSelection.visible = False
                tableBrowseSelection.visible = False
                page.update()

    page.title = "Calibre Data Manager"
    page.window_width = 1000
    page.window_height = 600
    page.window_title_bar_hidden = True
    page.window_title_bar_buttons_hidden = True
    page.window_resizable = False
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

    tableBrowseSelection = ft.Dropdown(
        label="Select Table to Browse",
        label_style=ft.TextStyle(color="#e1e3e3", weight=ft.FontWeight.BOLD),
        options=[
            ft.dropdown.Option("Stock Levels"),
            ft.dropdown.Option("Historical Sales"),
        ],
        on_change=tableSwitcher,
        expand=True,
        border_radius=10,
        border_color=ft.colors.TRANSPARENT,
        visible=True,
    )

    tableSearchSelection = ft.Dropdown(
        label="Select Table to Search",
        label_style=ft.TextStyle(color="#e1e3e3", weight=ft.FontWeight.BOLD),
        options=[
            ft.dropdown.Option("Stock Levels"),
            ft.dropdown.Option("Historical Sales"),
        ],
        visible=False,
        on_change=search,
        expand=True,
        border_radius=10,
        border_color=ft.colors.TRANSPARENT,
    )

    searchBar = ft.TextField(
        label="Press Enter to Search",
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
        visible=False,
        on_submit=search,
    )

    stockLevelsTable = ft.DataTable(
        bgcolor="#1b2628",
        border_radius=10,
        divider_thickness=0,
        heading_row_height=75,
        horizontal_lines=ft.border.BorderSide(0, "#004f58"),
        heading_text_style=ft.TextStyle(color="#e1e3e3", weight=ft.FontWeight.BOLD),
        data_text_style=ft.TextStyle(color="#e1e3e3"),
        visible=False,
    )

    historicalSalesTable = ft.DataTable(
        bgcolor="#1b2628",
        border_radius=10,
        divider_thickness=0,
        heading_row_height=75,
        horizontal_lines=ft.border.BorderSide(0, "#004f58"),
        heading_text_style=ft.TextStyle(color="#e1e3e3", weight=ft.FontWeight.BOLD),
        data_text_style=ft.TextStyle(color="#e1e3e3"),
        visible=False,
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
        columns=[ft.DataColumn(ft.Text(column)) for column in stockLevelsColumns],
        bgcolor="#1b2628",
        border_radius=10,
        visible=False,
        divider_thickness=0,
        heading_row_height=75,
        horizontal_lines=ft.border.BorderSide(0, "#004f58"),
        heading_text_style=ft.TextStyle(color="#e1e3e3", weight=ft.FontWeight.BOLD),
        data_text_style=ft.TextStyle(color="#e1e3e3"),
    )

    searchHistoricalSalesTable = ft.DataTable(
        columns=[ft.DataColumn(ft.Text(column)) for column in historicalSalesColumns],
        bgcolor="#1b2628",
        border_radius=10,
        visible=False,
        divider_thickness=0,
        heading_row_height=75,
        horizontal_lines=ft.border.BorderSide(0, "#004f58"),
        heading_text_style=ft.TextStyle(color="#e1e3e3", weight=ft.FontWeight.BOLD),
        data_text_style=ft.TextStyle(color="#e1e3e3"),
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

    onOrderTF = ft.TextField(
        label="Enter Quantity On Order",
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

    salesTF = ft.TextField(
        label="Enter Sales from 2018 to 2022 (separated by commas)",
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
                    [stockLevelsTable, historicalSalesTable],
                    scroll=True,
                    expand=True,
                    on_scroll=onScroll,
                ),
            ),
            ft.Tab(
                text="Search",
                icon=ft.icons.SEARCH_ROUNDED,
                content=ft.Container(
                    ft.Column(
                        [searchStockLevelsTable, searchHistoricalSalesTable],
                        scroll=True,
                        expand=True,
                    ),
                ),
            ),
            ft.Tab(text="Charts", icon=ft.icons.LINE_AXIS_ROUNDED),
            ft.Tab(
                text="Add / Edit Data",
                icon=ft.icons.EDIT_ROUNDED,
                content=ft.Container(
                    ft.Column(
                        [
                            stockCodeTF,
                            stockCATTF,
                            descriptionTF,
                            quantityTF,
                            moqTF,
                            onOrderTF,
                            salesTF,
                        ]
                    ),
                    expand=True,
                ),
            ),
        ],
        expand=True,
        on_change=search,
    )

    bar = ft.Column(
        [
            ft.Row([windowDragArea, btnClose]),
            ft.Row([tableBrowseSelection]),
            ft.Row([searchBar, tableSearchSelection]),
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
