import os
import psycopg2
from dotenv import load_dotenv
import flet as ft
from flet import RoundedRectangleBorder


load_dotenv()
connection = psycopg2.connect(os.getenv("dbURL"))
cursor = connection.cursor()

cursor.execute('SELECT NOW();')
time = cursor.fetchone()[0]

cursor.execute('SELECT version();')
version = cursor.fetchone()[0]


def main(page: ft.Page):
    page.title = "Calibre Data Manager"
    page.window_width = 500
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

    page.add(ft.Row(controls=[btnMenu, windowDragArea, btnClose]))


ft.app(target=main)


cursor.close()
connection.close()

print('Current time:', time)
print('PostgreSQL version:', version)