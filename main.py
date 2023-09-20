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
    def search(e):
        query = searchBar.value.strip().lower()
        if tabs.selected_index == 0:
            filteredStockLevels = [
                row
                for row in stockLevels
                if any(query in str(cell).lower() for cell in row)
            ]
            stockLevelsTable.rows = [
                ft.DataRow(cells=[ft.DataCell(ft.Text(cell)) for cell in row])
                for row in filteredStockLevels
            ]
        elif tabs.selected_index == 1:
            filteredHistoricalSales = [
                row
                for row in historicalSales
                if any(query in str(cell).lower() for cell in row)
            ]
            historicalSalesTable.rows = [
                ft.DataRow(cells=[ft.DataCell(ft.Text(cell)) for cell in row])
                for row in filteredHistoricalSales
            ]
        page.update()

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
                ft.MaterialState.HOVERED: ft.colors.RED_ACCENT_200,
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

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        divider_color=ft.colors.WHITE70,
        indicator_color=ft.colors.WHITE70,
        label_color=ft.colors.WHITE70,
        overlay_color=ft.colors.WHITE10,
        tabs=[
            ft.Tab(
                text="Stock Levels",
                icon=ft.icons.TABLE_ROWS,
                content=ft.Column([stockLevelsTable], scroll=True, expand=True),
            ),
            ft.Tab(
                text="Hisorical Sales",
                icon=ft.icons.TABLE_CHART,
                content=ft.Column([historicalSalesTable], scroll=True, expand=True),
            ),
            ft.Tab(text="Edit Tables", icon=ft.icons.EDIT),
        ],
        expand=True,
        on_change=search,
    )
    page.add(ft.Row([windowDragArea, btnClose]), ft.Row([searchBar]), tabs)


ft.app(target=main)


cursor.close()
connection.close()
