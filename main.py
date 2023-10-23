import os
import threading
import psycopg
from dotenv import load_dotenv
import flet as ft
from flet import RoundedRectangleBorder
from datetime import date

load_dotenv()
connection = psycopg.connect(os.getenv("DATABASE_URL"))
cursor = connection.cursor()

offset = 0
current_row = 0


def main(page: ft.Page):
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
        check_stock_code_exists(row)
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

    def refresh_table(e):
        stock_levels_table.rows = []
        global offset
        offset = 0
        add_data_to_table(
            stock_levels_table, fetch_stock_levels, 20, stock_levels_table.rows
        )
        return fetch_stock_levels(1)

    def show_banner(e, content):
        page.banner.open = True
        page.banner.content = ft.Text(content, color=ft.colors.ON_ERROR_CONTAINER)
        page.update()

    def close_banner(e):
        page.banner.open = False
        page.update()

    def show_search_bar(e):
        if search_bar.visible == False:
            search_bar.visible = True
            search_bar.focus()
            page.update()
        elif search_bar.visible == True:
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
            sql_query = f"SELECT d.*, stocklevels.quantity, stocklevels.moq, stocklevels.on_order, stockbalance.balance FROM products d INNER JOIN stocklevels using(stock_code) INNER JOIN stockbalance using(stock_id) WHERE {where_clause}"
            params = [f"%{query}%"] * len(columns_to_search)
            cursor.execute(sql_query, params)
            searchData = cursor.fetchall()
            rows = []
            for row in searchData:
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
        if forms.visible == True:
            forms.visible = False
            minimise.icon = ft.icons.ADD_ROUNDED
            page.update()
        else:
            forms.visible = True
            minimise.icon = ft.icons.REMOVE_ROUNDED
            page.update()

    def check_customer_exists(e):
        name = str(name_tf.value)
        cursor.execute("SELECT * FROM customers WHERE name = %s", (name,))
        if cursor.rowcount > 0:
            address_tf.visible = False
            address_tf.value = ""
            page.update()
        else:
            address_tf.visible = True
            page.update()

    def check_stock_code_exists(e):
        stock_code = str(stock_code_product_tf.value)
        cursor.execute(
            "SELECT stock_code FROM products WHERE stock_code = %s", (stock_code,)
        )
        if cursor.rowcount > 0:
            add_product_button.icon = ft.icons.UPDATE_ROUNDED
            page.update()
        else:
            add_product_button.icon = ft.icons.ADD_ROUNDED
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
        stockCode = (
            str(stock_code_product_tf.value)
            if stock_code_product_tf.value != ""
            else None
        )
        stockCAT = int(stock_cat_tf.value) if stock_cat_tf.value != "" else None
        description = str(description_tf.value) if description_tf.value != "" else None
        quantity = int(quantity_tf.value) if quantity_tf.value != "" else None
        moq = int(moq_tf.value) if moq_tf.value != "" else None
        if stockCode != None:
            cursor.execute("SELECT * FROM products WHERE stock_code = %s", (stockCode,))
            if cursor.rowcount > 0:
                cursor.execute(
                    "UPDATE products SET stock_cat = %s WHERE stock_code = %s",
                    (stockCAT, stockCode),
                ) if stockCAT != None else None
                connection.commit()
                cursor.execute(
                    "UPDATE products SET description = %s WHERE stock_code = %s",
                    (description, stockCode),
                ) if description != None else None
                connection.commit()
                cursor.execute(
                    "UPDATE stocklevels SET quantity = %s WHERE stock_code = %s",
                    (quantity, stockCode),
                ) if quantity != None else None
                connection.commit()
                cursor.execute(
                    "UPDATE stocklevels SET moq = %s WHERE stock_code = %s",
                    (moq, stockCode),
                ) if moq != None else None
                connection.commit()
                cursor.execute(
                    "Select stock_id FROM stocklevels WHERE stock_code = %s",
                    (stockCode,),
                )
                stockID = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT quantity FROM stocklevels WHERE stock_code = %s",
                    (stockCode,),
                )
                quantity = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT on_order FROM stocklevels WHERE stock_code = %s",
                    (stockCode,),
                )
                onOrder = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT moq FROM stocklevels WHERE stock_code = %s",
                    (stockCode,),
                )
                moq = int(cursor.fetchone()[0])
                cursor.execute(
                    "UPDATE stockbalance SET balance = %s WHERE stock_id = %s",
                    (quantity + moq - onOrder, stockID),
                )
                connection.commit()
            else:
                if (
                    stockCAT != None
                    and description != None
                    and quantity != None
                    and moq != None
                ):
                    cursor.execute(
                        "INSERT INTO products(stock_code, stock_cat, description) VALUES(%s, %s, %s)",
                        (stockCode, stockCAT, description),
                    )
                    connection.commit()
                    cursor.execute(
                        "INSERT INTO stocklevels(stock_code, moq, quantity, on_order) VALUES(%s, %s, %s, %s)",
                        (stockCode, moq, quantity, 0),
                    )
                    connection.commit()
                    cursor.execute(
                        "Select stock_id FROM stocklevels WHERE stock_code = %s",
                        (stockCode,),
                    )
                    stockID = int(cursor.fetchone()[0])
                    cursor.execute(
                        "SELECT on_order FROM stocklevels WHERE stock_code = %s",
                        (stockCode,),
                    )
                    onOrder = 0
                    cursor.execute(
                        "INSERT INTO stockbalance(stock_id, balance) VALUES(%s, %s)",
                        (stockID, quantity + moq - onOrder),
                    )
                    connection.commit()
                else:
                    show_banner(
                        e,
                        "Please fill in all fields as there is no stock code match",
                    )
                page.update()
        elif stockCode == None:
            show_banner(e, "Please fill in the stock code field")
            page.update()
        clear_product_form(e)
        refresh_table(e)
        search(e) if search_stock_levels_table.visible == True else None

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
            if cursor.rowcount > 0:
                if stock_code != None and quantity != None and name != None:
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
                else:
                    show_banner(e, "Please fill in all fields")
                page.update()
            else:
                if (
                    stock_code != None
                    and quantity != None
                    and name != None
                    and address != None
                ):
                    cursor.execute(
                        "INSERT INTO customers(name, address) VALUES(%s, %s)",
                        (name, address),
                    )
                    connection.commit()
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
                else:
                    show_banner(e, "Please fill in all fields")
                page.update()
        else:
            show_banner(e, "Stock Code does not exist")
            page.update()
        clear_order_form(e)
        refresh_table(e)
        search(e) if search_stock_levels_table.visible == True else None
        check_customer_exists(e)

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
                show_banner(e, "Stock Code does not exist")
                page.update()
        else:
            show_banner(e, "Please fill in the stock code field")
            page.update()
        clear_product_form(e)
        refresh_table(e)
        search(e) if search_stock_levels_table.visible == True else None

    def remove_order_data(e):
        try:
            order_id = int(order_id_tf.value)
        except:
            order_id = None
        if order_id != None:
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
                show_banner(e, "Order ID does not exist")
                page.update()
        else:
            show_banner(e, "Please fill in the order ID field")
            page.update()
        clear_order_form(e)
        refresh_table(e)
        search(e) if search_stock_levels_table.visible == True else None

    sem = threading.Semaphore()

    page.window_min_width = 950
    page.window_width = 950
    page.window_min_height = 500
    page.window_height = 900
    page.padding = 15
    page.theme = ft.Theme(
        visual_density=ft.ThemeVisualDensity.COMPACT,
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

    title_area = ft.Container(
        ft.Text(
            "Calibre Data Manager",
            color=ft.colors.ON_PRIMARY,
            text_align="left",
            weight=ft.FontWeight.BOLD,
        ),
        padding=10,
    )

    search_button = ft.IconButton(
        icon=ft.icons.SEARCH_ROUNDED,
        style=ft.ButtonStyle(
            color={ft.MaterialState.DEFAULT: ft.colors.ON_PRIMARY},
            shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=8)},
        ),
        on_click=show_search_bar,
    )

    search_bar = ft.TextField(
        expand=True,
        border_radius=8,
        text_style=ft.TextStyle(color=ft.colors.ON_PRIMARY_CONTAINER),
        border_color=ft.colors.TRANSPARENT,
        cursor_color=ft.colors.ON_PRIMARY_CONTAINER,
        bgcolor=ft.colors.PRIMARY_CONTAINER,
        content_padding=10,
        on_change=search,
        height=40,
        visible=False,
    )

    stock_levels_table = ft.DataTable(
        border=ft.border.all(2, ft.colors.SURFACE_VARIANT),
        border_radius=8,
        divider_thickness=0,
        heading_row_height=75,
        horizontal_lines=ft.border.BorderSide(1, ft.colors.PRIMARY),
        heading_text_style=ft.TextStyle(
            color=ft.colors.ON_BACKGROUND, weight=ft.FontWeight.BOLD
        ),
        data_text_style=ft.TextStyle(color=ft.colors.ON_BACKGROUND),
        data_row_color={ft.MaterialState.HOVERED: ft.colors.SURFACE_VARIANT},
        width=10000,
    )

    stock_levels_columns, _ = refresh_table(None)

    stock_levels_table.columns = [
        ft.DataColumn(ft.Text(str(column).capitalize().replace("_", " ")))
        for column in stock_levels_columns
    ]

    search_stock_levels_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(str(column).capitalize().replace("_", " ")))
            for column in stock_levels_columns
        ],
        border=ft.border.all(2, ft.colors.SURFACE_VARIANT),
        border_radius=8,
        divider_thickness=0,
        heading_row_height=75,
        horizontal_lines=ft.border.BorderSide(1, ft.colors.PRIMARY),
        heading_text_style=ft.TextStyle(
            color=ft.colors.ON_BACKGROUND, weight=ft.FontWeight.BOLD
        ),
        data_text_style=ft.TextStyle(color=ft.colors.ON_BACKGROUND),
        data_row_color={ft.MaterialState.HOVERED: ft.colors.SURFACE_VARIANT},
        visible=False,
        width=10000,
    )

    stock_code_product_tf = ft.TextField(
        hint_text="Stock Code",
        hint_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        expand=True,
        border_radius=8,
        text_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        label_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        border_color=ft.colors.TRANSPARENT,
        bgcolor=ft.colors.SURFACE_VARIANT,
        cursor_color=ft.colors.ON_SURFACE_VARIANT,
        on_change=check_stock_code_exists,
    )

    stock_code_order_tf = ft.TextField(
        hint_text="Stock Code",
        hint_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        expand=True,
        border_radius=8,
        text_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        label_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        border_color=ft.colors.TRANSPARENT,
        bgcolor=ft.colors.SURFACE_VARIANT,
        cursor_color=ft.colors.ON_SURFACE_VARIANT,
    )

    order_id_tf = ft.TextField(
        hint_text="Order ID",
        hint_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        expand=True,
        border_radius=8,
        text_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        label_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        border_color=ft.colors.TRANSPARENT,
        bgcolor=ft.colors.SURFACE_VARIANT,
        cursor_color=ft.colors.ON_SURFACE_VARIANT,
    )

    stock_cat_tf = ft.TextField(
        hint_text="Stock CAT",
        hint_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        expand=True,
        border_radius=8,
        text_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        label_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        border_color=ft.colors.TRANSPARENT,
        bgcolor=ft.colors.SURFACE_VARIANT,
        cursor_color=ft.colors.ON_SURFACE_VARIANT,
    )

    description_tf = ft.TextField(
        hint_text="Description",
        hint_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        expand=True,
        border_radius=8,
        text_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        label_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        border_color=ft.colors.TRANSPARENT,
        bgcolor=ft.colors.SURFACE_VARIANT,
        cursor_color=ft.colors.ON_SURFACE_VARIANT,
    )

    quantity_tf = ft.TextField(
        hint_text="Quantity",
        hint_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        expand=True,
        border_radius=8,
        text_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        label_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        border_color=ft.colors.TRANSPARENT,
        bgcolor=ft.colors.SURFACE_VARIANT,
        cursor_color=ft.colors.ON_SURFACE_VARIANT,
    )

    moq_tf = ft.TextField(
        hint_text="MOQ",
        hint_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        expand=True,
        border_radius=8,
        text_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        label_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        border_color=ft.colors.TRANSPARENT,
        bgcolor=ft.colors.SURFACE_VARIANT,
        cursor_color=ft.colors.ON_SURFACE_VARIANT,
    )

    order_quantity_tf = ft.TextField(
        hint_text="Quantity",
        hint_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        expand=True,
        border_radius=8,
        text_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        label_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        border_color=ft.colors.TRANSPARENT,
        bgcolor=ft.colors.SURFACE_VARIANT,
        cursor_color=ft.colors.ON_SURFACE_VARIANT,
    )

    name_tf = ft.TextField(
        hint_text="Customer Name",
        hint_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        expand=True,
        border_radius=8,
        text_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        label_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        border_color=ft.colors.TRANSPARENT,
        bgcolor=ft.colors.SURFACE_VARIANT,
        cursor_color=ft.colors.ON_SURFACE_VARIANT,
        on_change=check_customer_exists,
    )

    address_tf = ft.TextField(
        hint_text="Customer Address",
        hint_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        expand=True,
        border_radius=8,
        text_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        label_style=ft.TextStyle(color=ft.colors.ON_SURFACE_VARIANT),
        border_color=ft.colors.TRANSPARENT,
        bgcolor=ft.colors.SURFACE_VARIANT,
        cursor_color=ft.colors.ON_SURFACE_VARIANT,
    )

    add_product_button = ft.Container(
        ft.IconButton(
            icon=ft.icons.ADD_ROUNDED,
            style=ft.ButtonStyle(
                color={ft.MaterialState.DEFAULT: ft.colors.ON_PRIMARY},
                shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=8)},
            ),
            on_click=add_product_data,
        ),
        bgcolor=ft.colors.PRIMARY,
        border_radius=8,
    )

    add_order_button = ft.Container(
        ft.IconButton(
            icon=ft.icons.ADD_ROUNDED,
            style=ft.ButtonStyle(
                color={ft.MaterialState.DEFAULT: ft.colors.ON_PRIMARY},
                shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=8)},
            ),
            on_click=add_order_data,
        ),
        bgcolor=ft.colors.PRIMARY,
        border_radius=8,
    )

    delete_product_button = ft.Container(
        ft.IconButton(
            icon=ft.icons.DELETE_ROUNDED,
            style=ft.ButtonStyle(
                color={ft.MaterialState.DEFAULT: ft.colors.ON_PRIMARY},
                shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=8)},
            ),
            on_click=remove_product_data,
        ),
        bgcolor=ft.colors.PRIMARY,
        border_radius=8,
    )

    delete_order_button = ft.Container(
        ft.IconButton(
            icon=ft.icons.DELETE_ROUNDED,
            style=ft.ButtonStyle(
                color={ft.MaterialState.DEFAULT: ft.colors.ON_PRIMARY},
                shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=8)},
            ),
            on_click=remove_order_data,
        ),
        bgcolor=ft.colors.PRIMARY,
        border_radius=8,
    )

    clear_product_form_button = ft.Container(
        ft.IconButton(
            icon=ft.icons.CLEAR_ROUNDED,
            style=ft.ButtonStyle(
                color={ft.MaterialState.DEFAULT: ft.colors.ON_PRIMARY},
                shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=8)},
            ),
            on_click=clear_product_form,
        ),
        bgcolor=ft.colors.PRIMARY,
        border_radius=8,
    )

    clear_order_form_button = ft.Container(
        ft.IconButton(
            icon=ft.icons.CLEAR_ROUNDED,
            style=ft.ButtonStyle(
                color={ft.MaterialState.DEFAULT: ft.colors.ON_PRIMARY},
                shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=8)},
            ),
            on_click=clear_product_form,
        ),
        bgcolor=ft.colors.PRIMARY,
        border_radius=8,
    )
    minimise = ft.IconButton(
        ft.icons.REMOVE_ROUNDED,
        style=ft.ButtonStyle(
            color={ft.MaterialState.DEFAULT: ft.colors.PRIMARY},
            shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=8)},
        ),
        on_click=minimise_forms,
    )

    bar = ft.Container(
        ft.Row([title_area, search_button, search_bar], alignment="center"),
        padding=10,
        bgcolor=ft.colors.PRIMARY,
        expand=True,
        border_radius=ft.border_radius.only(top_left=8, top_right=8),
    )

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
                        scroll=True,
                    ),
                    expand=True,
                    border=ft.border.all(2, ft.colors.SURFACE_VARIANT),
                    border_radius=8,
                    padding=15,
                    height=320,
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
                        scroll=True,
                    ),
                    expand=True,
                    border=ft.border.all(2, ft.colors.SURFACE_VARIANT),
                    border_radius=8,
                    padding=15,
                    height=320,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
            ]
        ),
        expand=True,
        alignment=ft.Alignment(0, -1),
    )

    page.add(
        ft.Container(bar),
        forms,
        ft.Container(
            ft.Column(
                [ft.Divider(color=ft.colors.SURFACE_VARIANT, thickness=2), minimise]
            ),
            padding=10,
        ),
        ft.Column(
            [
                ft.Container(
                    stock_levels_table,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                search_stock_levels_table,
            ],
            scroll=True,
            on_scroll=on_scroll,
            expand=True,
            alignment=ft.Alignment(0, -1),
        ),
    )


if __name__ == "__main__":
    ft.app(target=main)

cursor.close()
connection.close()
