import os
import threading
import psycopg
from dotenv import load_dotenv
import flet as ft
from flet import RoundedRectangleBorder
from controls import FormField, Table, FormButton
from datetime import date

load_dotenv()
connection = psycopg.connect(os.getenv("DATABASE_URL"))
cursor = connection.cursor()

offset = 0
current_row = 0


def main(page: ft.Page) -> None:
    def fetch_stock_levels(limit):
        global offset
        cursor.execute(
            "SELECT d.*, stocklevels.quantity, stocklevels.moq, stocklevels.on_order, stockbalance.balance FROM products d INNER JOIN stocklevels using(stock_code) INNER JOIN stockbalance using(stock_id) LIMIT %s OFFSET %s",
            (limit, offset),
        )
        stock_levels = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description if desc[0] != "stock_id"]
        offset += limit
        return column_names, stock_levels

    def load_data(row):
        stock_code_product_tf.value = row[0]
        stock_cat_tf.value = row[1]
        description_tf.value = row[2]
        quantity_tf.value = row[3]
        moq_tf.value = row[4]
        stock_code_order_tf.value = row[0]
        page.update()

    def add_data_to_table(table: ft.DataTable, fetch_function, limit, rows):
        column_names, data = fetch_function(limit=limit)
        new_rows = []
        for row in data:
            new_rows.append(
                ft.DataRow(
                    cells=[ft.DataCell(ft.Text(cell)) for cell in row],
                    on_select_changed=lambda e, row=row: load_data(row),
                )
            )
        rows += new_rows
        table.rows = rows
        page.update()

    def on_scroll(e: ft.OnScrollEvent):
        if e.pixels >= e.max_scroll_extent - 300:
            if sem.acquire(blocking=False):
                try:
                    add_data_to_table(
                        stock_levels_table,
                        fetch_stock_levels,
                        10,
                        stock_levels_table.rows,
                    )
                finally:
                    sem.release()

    def refresh_table():
        stock_levels_table.rows = []
        global offset
        offset = 0
        add_data_to_table(
            stock_levels_table, fetch_stock_levels, 20, stock_levels_table.rows
        )
        return fetch_stock_levels(1)

    def show_banner(content):
        page.banner.open = True
        page.banner.content = ft.Text(content, color=ft.colors.ON_ERROR_CONTAINER)
        page.update()

    def close_banner(e):
        page.banner.open = False
        page.update()

    def show_search_bar(e):
        if not search_bar.visible:
            search_bar.visible = True
            search_bar.focus()
            page.update()
        elif search_bar.visible:
            search_bar.visible = False
            search_bar.value = ""
            search(e)
            page.update()

    def search(e):
        query = str(search_bar.value.strip())
        if query != "":
            search_stock_levels_table.visible = True
            stock_levels_table.visible = False
            columns_to_search = [column for column in stock_levels_columns]
            conditions = [
                f"CAST({column} as TEXT) LIKE %s" for column in columns_to_search
            ]
            where_clause = " OR ".join(conditions)
            sql_query: str = f"SELECT d.*, stocklevels.quantity, stocklevels.moq, stocklevels.on_order, stockbalance.balance FROM products d INNER JOIN stocklevels using(stock_code) INNER JOIN stockbalance using(stock_id) WHERE {where_clause}"
            params = [f"%{query}%"] * len(columns_to_search)
            cursor.execute(sql_query, params)
            search_data = cursor.fetchall()
            rows = []
            for row in search_data:
                rows.append(
                    ft.DataRow(
                        cells=[ft.DataCell(ft.Text(str(cell))) for cell in row],
                        on_select_changed=lambda e, row=row: load_data(row),
                    )
                )
                search_stock_levels_table.rows = rows
            page.update()
        else:
            search_stock_levels_table.rows = []
            search_stock_levels_table.visible = False
            stock_levels_table.visible = True
            page.update()

    def minimise_forms(e):
        if forms.visible:
            forms.visible = False
            minimise.icon = ft.icons.ADD_ROUNDED
            page.update()
        else:
            forms.visible = True
            minimise.icon = ft.icons.REMOVE_ROUNDED
            page.update()

    def clear_product_form(e):
        stock_code_product_tf.value = ""
        stock_cat_tf.value = ""
        description_tf.value = ""
        quantity_tf.value = ""
        moq_tf.value = ""
        page.update()

    def clear_order_form(e):
        stock_code_order_tf.value = ""
        order_quantity_tf.value = ""
        name_tf.value = ""
        address_tf.value = ""
        page.update()

    def add_product_data(e):
        stock_code = (
            str(stock_code_product_tf.value)
            if stock_code_product_tf.value != ""
            else None
        )
        stock_cat = int(stock_cat_tf.value) if stock_cat_tf.value != "" else None
        description = str(description_tf.value) if description_tf.value != "" else None
        quantity = int(quantity_tf.value) if quantity_tf.value != "" else None
        moq = int(moq_tf.value) if moq_tf.value != "" else None
        if stock_code is not None:
            cursor.execute("SELECT * FROM products WHERE stock_code = %s", (stock_code,))
            if cursor.rowcount > 0:
                cursor.execute(
                    "UPDATE products SET stock_cat = %s WHERE stock_code = %s",
                    (stock_cat, stock_code),
                ) if stock_cat is not None else None
                connection.commit()
                cursor.execute(
                    "UPDATE products SET description = %s WHERE stock_code = %s",
                    (description, stock_code),
                ) if description is not None else None
                connection.commit()
                cursor.execute(
                    "UPDATE stocklevels SET quantity = %s WHERE stock_code = %s",
                    (quantity, stock_code),
                ) if quantity is not None else None
                connection.commit()
                cursor.execute(
                    "UPDATE stocklevels SET moq = %s WHERE stock_code = %s",
                    (moq, stock_code),
                ) if moq is not None else None
                connection.commit()
                cursor.execute(
                    "Select stock_id FROM stocklevels WHERE stock_code = %s",
                    (stock_code,),
                )
                stock_id = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT quantity FROM stocklevels WHERE stock_code = %s",
                    (stock_code,),
                )
                quantity = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT on_order FROM stocklevels WHERE stock_code = %s",
                    (stock_code,),
                )
                on_order = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT moq FROM stocklevels WHERE stock_code = %s",
                    (stock_code,),
                )
                moq = int(cursor.fetchone()[0])
                cursor.execute(
                    "UPDATE stockbalance SET balance = %s WHERE stock_id = %s",
                    (quantity + moq - on_order, stock_id),
                )
                connection.commit()
            else:
                if stock_cat is None or description is None or quantity is None or moq is None:
                    show_banner(
                        "Please fill in all fields as there is no stock code match",
                    )
                else:
                    cursor.execute(
                        "INSERT INTO products(stock_code, stock_cat, description) VALUES(%s, %s, %s)",
                        (stock_code, stock_cat, description),
                    )
                    connection.commit()
                    cursor.execute(
                        "INSERT INTO stocklevels(stock_code, moq, quantity, on_order) VALUES(%s, %s, %s, %s)",
                        (stock_code, moq, quantity, 0),
                    )
                    connection.commit()
                    cursor.execute(
                        "Select stock_id FROM stocklevels WHERE stock_code = %s",
                        (stock_code,),
                    )
                    stock_id = int(cursor.fetchone()[0])
                    cursor.execute(
                        "SELECT on_order FROM stocklevels WHERE stock_code = %s",
                        (stock_code,),
                    )
                    on_order = 0
                    cursor.execute(
                        "INSERT INTO stockbalance(stock_id, balance) VALUES(%s, %s)",
                        (stock_id, quantity + moq - on_order),
                    )
                    connection.commit()
                page.update()
        elif stock_code is None:
            show_banner("Please fill in the stock code field")
            page.update()
        clear_product_form(e)
        refresh_table()
        if search_stock_levels_table.visible:
            search(e)

    def add_order_data(e):
        stock_code = (
            str(stock_code_order_tf.value) if stock_code_order_tf.value != "" else None
        )
        quantity = (
            int(order_quantity_tf.value) if order_quantity_tf.value != "" else None
        )
        name = str(name_tf.value) if name_tf.value != "" else None
        address = str(address_tf.value) if address_tf.value != "" else None
        cursor.execute("SELECT * FROM products WHERE stock_code = %s", (stock_code,))
        if cursor.rowcount > 0:
            cursor.execute("SELECT * FROM customers WHERE name = %s", (name,))
            if cursor.rowcount == 0:
                if stock_code is None or quantity is None or name is None or address is None:
                    show_banner("Please fill in all fields")
                else:
                    cursor.execute(
                        "INSERT INTO customers(name, address) VALUES(%s, %s)",
                        (name, address),
                    )
                    connection.commit()
            try:
                if stock_code is None or quantity is None or name is None:
                    show_banner("Please fill in all fields")
                else:
                    cursor.execute(
                        "SELECT customer_id FROM customers WHERE name = %s",
                        (name,),
                    )
                    customer_id = int(cursor.fetchone()[0])
                    cursor.execute(
                        "INSERT INTO orders(stock_code, order_quantity, date, customer_id) VALUES(%s, %s, %s,%s)",
                        (stock_code, quantity, date.today(), customer_id),
                    )
                    connection.commit()
                    cursor.execute(
                        "SELECT on_order FROM stocklevels WHERE stock_code = %s",
                        (stock_code,),
                    )
                    on_order = int(cursor.fetchone()[0])
                    cursor.execute(
                        "UPDATE stocklevels SET on_order = %s WHERE stock_code = %s",
                        (on_order + quantity, stock_code),
                    )
                    connection.commit()
                    on_order = on_order + quantity
                    cursor.execute(
                        "SELECT quantity FROM stocklevels WHERE stock_code = %s",
                        (stock_code,),
                    )
                    quantity = int(cursor.fetchone()[0])
                    cursor.execute(
                        "SELECT moq FROM stocklevels WHERE stock_code = %s",
                        (stock_code,),
                    )
                    moq = int(cursor.fetchone()[0])
                    cursor.execute(
                        "Select stock_id FROM stocklevels WHERE stock_code = %s",
                        (stock_code,),
                    )
                    stock_id = int(cursor.fetchone()[0])
                    cursor.execute(
                        "UPDATE stockbalance SET balance = %s WHERE stock_id = %s",
                        (quantity + moq - on_order, stock_id),
                    )
                    connection.commit()
            except psycopg.errors.ForeignKeyViolation:
                show_banner("Customer does not exist")
                page.update()
            finally:
                page.update()
        else:
            show_banner("Stock Code does not exist")
            page.update()
        clear_order_form(e)
        refresh_table()
        if search_stock_levels_table.visible:
            search(e)

    def remove_product_data(e):
        stock_code = str(stock_code_product_tf.value)
        if stock_code != "":
            cursor.execute(
                "SELECT * FROM products WHERE stock_code = %s", (stock_code,)
            )
            if cursor.rowcount > 0:
                cursor.execute(
                    "SELECT stock_id FROM stocklevels WHERE stock_code = %s",
                    (stock_code,),
                )
                stock_id = int(cursor.fetchone()[0])
                cursor.execute(
                    "DELETE FROM stockbalance WHERE stock_id = %s", (stock_id,)
                )
                connection.commit()
                cursor.execute(
                    "DELETE FROM stocklevels WHERE stock_code = %s", (stock_code,)
                )
                connection.commit()
                cursor.execute(
                    "DELETE FROM orders WHERE stock_code = %s", (stock_code,)
                )
                connection.commit()
                cursor.execute(
                    "DELETE FROM products WHERE stock_code = %s", (stock_code,)
                )
                connection.commit()
            else:
                show_banner("Stock Code does not exist")
                page.update()
        else:
            show_banner("Please fill in the stock code field")
            page.update()
        clear_product_form(e)
        refresh_table()
        if search_stock_levels_table.visible:
            search(e)

    def remove_order_data(e):
        order_id = int(order_id_tf.value) if order_id_tf.value is not None else None
        if order_id is not None:
            cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
            if cursor.rowcount > 0:
                cursor.execute(
                    "SELECT stock_code FROM orders WHERE order_id = %s", (order_id,)
                )
                stock_code = str(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT on_order FROM stocklevels WHERE stock_code = %s",
                    (stock_code,),
                )
                on_order = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT order_quantity FROM orders WHERE order_id = %s", (order_id,)
                )
                order_quantity = int(cursor.fetchone()[0])
                cursor.execute(
                    "UPDATE stocklevels SET on_order = %s WHERE stock_code = %s",
                    (on_order - order_quantity, stock_code),
                )
                connection.commit()
                on_order = on_order - order_quantity
                cursor.execute(
                    "SELECT quantity FROM stocklevels WHERE stock_code = %s",
                    (stock_code,),
                )
                quantity = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT moq FROM stocklevels WHERE stock_code = %s", (stock_code,)
                )
                moq = int(cursor.fetchone()[0])
                cursor.execute(
                    "Select stock_id FROM stocklevels WHERE stock_code = %s",
                    (stock_code,),
                )
                stock_id = int(cursor.fetchone()[0])
                cursor.execute(
                    "UPDATE stockbalance SET balance = %s WHERE stock_id = %s",
                    (quantity + moq - on_order, stock_id),
                )
                connection.commit()
                cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
                connection.commit()
            else:
                show_banner("Order ID does not exist")
                page.update()
        else:
            show_banner("Please fill in the order ID field")
            page.update()
        clear_order_form(e)
        refresh_table()
        if search_stock_levels_table.visible:
            search(e)

    sem = threading.Semaphore()

    page.window_min_width = 950
    page.window_width = 950
    page.window_min_height = 500
    page.window_height = 1000
    page.padding = 15
    page.theme = ft.Theme(
        use_material3=True,
        color_scheme=ft.ColorScheme(
            primary="#00677f",
            on_primary="#ffffff",
            primary_container="#b6eaff",
            on_primary_container="#001f28",
            secondary="#4c626a",
            on_secondary="#ffffff",
            secondary_container="#cfe6f1",
            on_secondary_container="#071e26",
            tertiary="#5a5c7e",
            on_tertiary="#ffffff",
            tertiary_container="#e0e0ff",
            on_tertiary_container="#171937",
            error="#ba1a1a",
            on_error="#ffffff",
            error_container="#ffdad6",
            on_error_container="#410002",
            background="#fbfcfe",
            on_background="#191c1d",
            surface="#fbfcfe",
            on_surface="#191c1d",
            outline="#70787c",
            surface_variant="#dbe4e8",
            on_surface_variant="#40484c",
        ),
    )
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.colors.BACKGROUND
    page.banner = ft.Banner(
        bgcolor=ft.colors.ERROR_CONTAINER,
        leading=ft.Icon(
            ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.ON_ERROR_CONTAINER
        ),
        actions=[
            ft.IconButton(
                icon=ft.icons.CLOSE,
                style=ft.ButtonStyle(
                    color={
                        ft.MaterialState.DEFAULT: ft.colors.ON_ERROR_CONTAINER,
                    },
                    shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=8)},
                ),
                on_click=close_banner,
            )
        ],
    )

    search_button = FormButton(ft.icons.SEARCH_ROUNDED, show_search_bar, ft.colors.ON_PRIMARY)

    search_bar = FormField("Search", ft.colors.ON_PRIMARY, ft.colors.TRANSPARENT, ft.colors.ON_PRIMARY, search, False)

    stock_levels_table = Table()

    stock_levels_columns, _ = refresh_table()

    stock_levels_table.columns = [
        ft.DataColumn(ft.Text(str(column).capitalize().replace("_", " ")))
        for column in stock_levels_columns
    ]

    search_stock_levels_table = Table()

    search_stock_levels_table.columns = [
        ft.DataColumn(ft.Text(str(column).capitalize().replace("_", " ")))
        for column in stock_levels_columns
    ]

    stock_code_product_tf = FormField("Stock Code", ft.colors.TRANSPARENT, ft.colors.SURFACE_VARIANT,
                                      ft.colors.ON_SURFACE_VARIANT, None, True)
    stock_code_order_tf = FormField("Stock Code", ft.colors.TRANSPARENT, ft.colors.SURFACE_VARIANT,
                                    ft.colors.ON_SURFACE_VARIANT, None, True)
    order_id_tf = FormField("Order ID", ft.colors.TRANSPARENT, ft.colors.SURFACE_VARIANT, ft.colors.ON_SURFACE_VARIANT,
                            None, True)
    stock_cat_tf = FormField("Stock Category", ft.colors.TRANSPARENT, ft.colors.SURFACE_VARIANT,
                             ft.colors.ON_SURFACE_VARIANT, None, True)
    description_tf = FormField("Description", ft.colors.TRANSPARENT, ft.colors.SURFACE_VARIANT,
                               ft.colors.ON_SURFACE_VARIANT, None, True)
    quantity_tf = FormField("Quantity", ft.colors.TRANSPARENT, ft.colors.SURFACE_VARIANT, ft.colors.ON_SURFACE_VARIANT,
                            None, True)
    moq_tf = FormField("MOQ", ft.colors.TRANSPARENT, ft.colors.SURFACE_VARIANT, ft.colors.ON_SURFACE_VARIANT, None,
                       True)
    order_quantity_tf = FormField("Order Quantity", ft.colors.TRANSPARENT, ft.colors.SURFACE_VARIANT,
                                  ft.colors.ON_SURFACE_VARIANT, None, True)
    name_tf = FormField("Customer Name", ft.colors.TRANSPARENT, ft.colors.SURFACE_VARIANT, ft.colors.ON_SURFACE_VARIANT,
                        None, True)
    address_tf = FormField("Customer Address", ft.colors.TRANSPARENT, ft.colors.SURFACE_VARIANT,
                           ft.colors.ON_SURFACE_VARIANT, None, True)

    add_product_button = ft.Container(FormButton(ft.icons.ADD_ROUNDED, add_product_data, ft.colors.ON_PRIMARY),
                                      bgcolor=ft.colors.PRIMARY, border_radius=8)
    add_order_button = ft.Container(FormButton(ft.icons.ADD_ROUNDED, add_order_data, ft.colors.ON_PRIMARY),
                                    bgcolor=ft.colors.PRIMARY, border_radius=8)
    delete_product_button = ft.Container(FormButton(ft.icons.DELETE_ROUNDED, remove_product_data, ft.colors.ON_PRIMARY),
                                         bgcolor=ft.colors.PRIMARY, border_radius=8)
    delete_order_button = ft.Container(FormButton(ft.icons.DELETE_ROUNDED, remove_order_data, ft.colors.ON_PRIMARY),
                                       bgcolor=ft.colors.PRIMARY, border_radius=8)
    clear_product_form_button = ft.Container(
        FormButton(ft.icons.CLEAR_ROUNDED, clear_product_form, ft.colors.ON_PRIMARY), bgcolor=ft.colors.PRIMARY,
        border_radius=8)
    clear_order_form_button = ft.Container(FormButton(ft.icons.CLEAR_ROUNDED, clear_order_form, ft.colors.ON_PRIMARY),
                                           bgcolor=ft.colors.PRIMARY, border_radius=8)
    minimise = FormButton(ft.icons.REMOVE_ROUNDED, minimise_forms, ft.colors.PRIMARY)

    forms = ft.Container(
        ft.Row(
            [
                ft.Container(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        "Add / Edit Product",
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.ON_BACKGROUND,
                                    ),
                                ]
                            ),
                            ft.Row(
                                [
                                    stock_code_product_tf,
                                    add_product_button,
                                    delete_product_button,
                                    clear_product_form_button,
                                ]
                            ),
                            ft.Row([description_tf]),
                            ft.Row([stock_cat_tf]),
                            ft.Row([quantity_tf, moq_tf]),
                        ],
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    expand=True,
                    border=ft.border.all(2, ft.colors.SURFACE_VARIANT),
                    border_radius=8,
                    padding=15,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                ft.Container(
                    ft.Column(
                        [
                            ft.Text(
                                "Add Order",
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.ON_BACKGROUND,
                            ),
                            ft.Row(
                                [
                                    order_id_tf,
                                    add_order_button,
                                    delete_order_button,
                                    clear_order_form_button,
                                ]
                            ),
                            ft.Row([stock_code_order_tf, order_quantity_tf]),
                            ft.Row([name_tf]),
                            ft.Row([address_tf]),
                        ],
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    expand=True,
                    border=ft.border.all(2, ft.colors.SURFACE_VARIANT),
                    border_radius=8,
                    padding=15,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
            ]
        ),
    )

    page.add(
        ft.Container(
            ft.Row(
                [
                    ft.Container(
                        ft.Text(
                            "Calibre Data Manager",
                            color=ft.colors.ON_PRIMARY,
                            text_align=ft.TextAlign.LEFT,
                            weight=ft.FontWeight.BOLD,
                        ),
                        padding=10,
                    ),
                    search_button,
                    search_bar,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=10,
            bgcolor=ft.colors.PRIMARY,
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
            height=75,
        ),
        forms,
        ft.Column(
            [ft.Divider(color=ft.colors.SURFACE_VARIANT, thickness=2), minimise],

        ),
        ft.Column(
            [
                ft.Container(
                    stock_levels_table,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                ft.Container(
                    search_stock_levels_table,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            on_scroll=on_scroll,
            expand=True,
        ),
    )


if __name__ == "__main__":
    ft.app(target=main)

cursor.close()
connection.close()
