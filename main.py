import os
import psycopg2
from dotenv import load_dotenv
import flet as ft
from flet import RoundedRectangleBorder


load_dotenv()
connection = psycopg2.connect(os.getenv("dbURL"))
cursor = connection.cursor()


def fetchStockLevels():
    cursor.execute("SELECT * FROM stocklevels")
    stockLevels = cursor.fetchall()
    columnNames = [desc[0] for desc in cursor.description]
    return columnNames, stockLevels


def fetchHisoricalSales():
    cursor.execute("SELECT * FROM historicalsales")
    historicalSales = cursor.fetchall()
    columnNames = [desc[0] for desc in cursor.description]
    return columnNames, historicalSales


def main(page: ft.Page):
    def dropDownChanged(e):
        if tableSelection.value == "Stock Levels":
            page.clean()
            page.add(
                ft.Row(controls=[btnMenu, windowDragArea, btnClose]),
                ft.Row(controls=[tableSelection]),
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[stockLevelsTable],
                            scroll=True,
                        ),
                    ],
                    scroll=True,
                    expand=True,
                ),
            )
        elif tableSelection.value == "Historical Sales":
            page.clean()
            page.add(
                ft.Row(controls=[btnMenu, windowDragArea, btnClose]),
                ft.Row(controls=[tableSelection]),
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[historicalSalesTable],
                            scroll=True,
                        ),
                    ],
                    scroll=True,
                    expand=True,
                ),
            )
        page.update()

    page.title = "Calibre Data Manager"
    page.window_width = 750
    page.window_height = 500
    page.window_title_bar_hidden = True
    page.window_title_bar_buttons_hidden = True

    windowDragArea = ft.WindowDragArea(
        ft.Container(
            ft.Text("Calibre Data Manager", color=ft.colors.WHITE70, size=15),
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
                ft.MaterialState.HOVERED: ft.colors.RED_ACCENT_200,
            },
            shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=10)},
            bgcolor=ft.colors.BLACK54,
        ),
        on_click=lambda _: page.window_close(),
    )

    btnMenu = ft.PopupMenuButton(
        items=[
            ft.PopupMenuItem(icon=ft.icons.SEARCH, text="Search Database"),
            ft.PopupMenuItem(icon=ft.icons.DATA_ARRAY, text="Edit Database"),
            ft.PopupMenuItem(icon=ft.icons.AUTO_GRAPH, text="View Statistics"),
        ],
    )

    tableSelection = ft.Dropdown(
        on_change=dropDownChanged,
        width=200,
        border_radius=10,
        hint_text="Select Table",
        options=[
            ft.dropdown.Option("Stock Levels"),
            ft.dropdown.Option("Historical Sales"),
        ],
    )

    columnNames, stockLevels = fetchStockLevels()
    rows = []
    for row in stockLevels:
        rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(cell)) for cell in row]))

    stockLevelsTable = ft.DataTable(
        columns=[ft.DataColumn(ft.Text(columnName)) for columnName in columnNames],
        rows=rows,
        bgcolor=ft.colors.BLACK54,
        border_radius=10,
    )

    columnNames, historicalSales = fetchHisoricalSales()
    rows = []
    for row in historicalSales:
        rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(cell)) for cell in row]))

    historicalSalesTable = ft.DataTable(
        columns=[ft.DataColumn(ft.Text(columnName)) for columnName in columnNames],
        rows=rows,
        bgcolor=ft.colors.BLACK54,
        border_radius=10,
    )

    page.add(
        ft.Row(controls=[btnMenu, windowDragArea, btnClose]),
        ft.Row(
            controls=[tableSelection],
        ),
    )


ft.app(target=main)


cursor.close()
connection.close()
