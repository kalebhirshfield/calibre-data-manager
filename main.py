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
                ft.Row(controls=[windowDragArea, btnClose]),
                ft.Row(controls=[tableSelection, searchBar]),
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
                ft.Row(controls=[windowDragArea, btnClose]),
                ft.Row(controls=[tableSelection, searchBar]),
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

    def navigateTo(section):
        if section == "Search":
            # Handle navigation to the Search section
            pass
        elif section == "Edit":
            # Handle navigation to the Edit section
            pass
        elif section == "Statistics":
            # Handle navigation to the View Statistics section
            pass

    def search(e):
        query = searchBar.value.strip().lower()
        if tableSelection.value == "Stock Levels":
            filteredStockLevels = [
                row
                for row in stockLevels
                if any(query in str(cell).lower() for cell in row)
            ]
            stockLevelsTable.rows = [
                ft.DataRow(cells=[ft.DataCell(ft.Text(cell)) for cell in row])
                for row in filteredStockLevels
            ]
        elif tableSelection.value == "Historical Sales":
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

    windowDragArea = ft.WindowDragArea(
        ft.Container(
            ft.Text(
                "Calibre Data Manager",
                color=ft.colors.WHITE70,
                size=20,
                text_align="center",
            ),
            bgcolor=ft.colors.BLACK54,
            padding=10,
            border_radius=50,
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
            shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=50)},
        ),
        on_click=lambda _: page.window_close(),
    )

    navRail = ft.NavigationRail(
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.SEARCH,
                label="Search Database",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.DATA_ARRAY,
                label="Edit Database",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.AUTO_GRAPH,
                label="View Statistics",
            ),
        ],
        on_change=lambda e: navigateTo(e.control.selected_index),
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

    searchBar = ft.TextField(
        label="Search",
        expand=True,
        border_radius=10,
        prefix_icon=ft.icons.SEARCH,
        on_change=search,
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
        ft.Column(
            controls=[
                ft.Row(controls=[windowDragArea, btnClose]),
                ft.Row(
                    controls=[tableSelection, searchBar],
                ),
            ]
        ),
    )


ft.app(target=main)


cursor.close()
connection.close()
