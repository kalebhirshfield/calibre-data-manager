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


def main(page: ft.Page):
    page.title = "Calibre Data Manager"
    page.window_width = 830
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

    columnNames, stockLevels = fetchStockLevels()
    rows = []
    for row in stockLevels:
        rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(cell)) for cell in row]))

    stockLevelsTable = ft.DataTable(
        columns=[ft.DataColumn(ft.Text(columnName)) for columnName in columnNames],
        rows=rows,
        bgcolor=ft.colors.BLACK54,
        border_radius=10,
        data_row_height=60,
    )

    page.add(
        ft.Row(controls=[btnMenu, windowDragArea, btnClose]),
        ft.Column(controls=[stockLevelsTable], expand=True, scroll=True),
    )


ft.app(target=main)


cursor.close()
connection.close()
