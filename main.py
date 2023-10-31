import os
import threading
from datetime import date

import matplotlib
import matplotlib.pyplot as plt
import psycopg
from dotenv import load_dotenv
from flet import ClipBehavior, MainAxisAlignment, MaterialState
from flet import Column, Row, Container, DataTable, DataColumn, DataRow, DataCell
from flet import FontWeight, IconButton, ButtonStyle, RoundedRectangleBorder, Padding
from flet import Page, View, Text, Icon, Theme, ThemeMode, ColorScheme, Banner
from flet import ScrollMode, OnScrollEvent
from flet import icons, colors, border, app, border_radius, matplotlib_chart

from controls import FormField, LoginField, Table, FormButton

matplotlib.use("svg")

load_dotenv()
connection = psycopg.connect(os.getenv("DATABASE_URL"))
cursor = connection.cursor()

offset = 0
current_row = 0
admin = False
chart = None


def main(page: Page) -> None:
    def fetch_stock_levels(limit) -> tuple | int:
        global offset
        cursor.execute(
            "SELECT d.*, stocklevels.quantity, stocklevels.moq, stocklevels.on_order, stockbalance.balance\
            FROM products d INNER JOIN stocklevels using(stock_code) INNER JOIN stockbalance using(stock_id)\
            LIMIT %s OFFSET %s",
            (limit, offset),
        )
        stock_levels = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description if desc[0] != "stock_id"]
        offset += limit
        return column_names, stock_levels

    def load_data(row) -> None:
        stock_code_product_tf.value = row[0]
        stock_cat_tf.value = row[1]
        description_tf.value = row[2]
        quantity_tf.value = row[3]
        moq_tf.value = row[4]
        stock_code_order_tf.value = row[0]
        page.update()

    def add_data_to_table(
        table: DataTable, fetch_function, limit, rows, row=None
    ) -> None:
        column_names, data = fetch_function(limit=limit)
        new_rows = []
        for row in data:
            new_rows.append(
                DataRow(
                    cells=[DataCell(Text(cell)) for cell in row],
                    on_select_changed=lambda e, selected_row=row: load_data(
                        selected_row
                    ),
                )
            )
        rows += new_rows
        table.rows = rows
        page.update()

    def on_scroll(e: OnScrollEvent) -> None:
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

    def refresh_table() -> tuple | int:
        stock_levels_table.rows = []
        global offset
        offset = 0
        add_data_to_table(
            stock_levels_table, fetch_stock_levels, 20, stock_levels_table.rows
        )
        return fetch_stock_levels(1)

    def show_banner(content) -> None:
        page.banner.open = True
        page.banner.content = Text(content, color=colors.ON_ERROR_CONTAINER)
        page.update()

    def close_banner(_) -> None:
        page.banner.open = False
        page.update()

    def login(e) -> None:
        username = str(username_tf.value) if username_tf.value != "" else None
        password = str(password_tf.value) if password_tf.value != "" else None
        user_details.content = Row(
            [
                Text(
                    value=username,
                    color=colors.ON_PRIMARY,
                    weight=FontWeight.BOLD,
                ),
                logout_button,
            ],
            alignment=MainAxisAlignment.CENTER,
            expand=True,
        )
        if username != "" and password != "":
            cursor.execute(
                "SELECT * FROM users WHERE username = %s AND password = %s",
                (username, password),
            )
            if cursor.rowcount > 0:
                global admin
                admin = True
                page.route = "/"
                route_change(e)
            else:
                show_banner("Incorrect username or password")
        else:
            show_banner("Please fill in all fields")
        username_tf.value = ""
        password_tf.value = ""
        page.update()

    def logout(e) -> None:
        global admin
        admin = False
        page.route = "/login"
        route_change(e)
        page.update()

    def display_product_chart(_) -> None:
        global chart
        cursor.execute(
            "SELECT stock_cat, SUM(quantity) FROM products INNER JOIN stocklevels using(stock_code) GROUP BY stock_cat"
        )
        data = cursor.fetchall()
        x = []
        y = []
        for row in data:
            x.append(row[0])
            y.append(row[1])
        fig, ax = plt.subplots()
        ax.bar(x, y, color="#00677f")
        ax.set_xlabel("Stock Category")
        ax.set_ylabel("Quantity")
        ax.set_title("Stock Category vs Quantity")
        ax.set_facecolor("#fbfcfe")
        ax.tick_params(axis="x", colors="#191c1d")
        ax.tick_params(axis="y", colors="#191c1d")
        ax.spines["bottom"].set_color("#dbe4e8")
        ax.spines["top"].set_color("#dbe4e8")
        ax.spines["left"].set_color("#dbe4e8")
        ax.spines["right"].set_color("#dbe4e8")
        ax.xaxis.label.set_color("#191c1d")
        ax.yaxis.label.set_color("#191c1d")
        ax.title.set_color("#191c1d")
        chart = matplotlib_chart.MatplotlibChart(fig, transparent=True)
        page.route = "/chart"
        route_change(_)

    def display_order_chart(_) -> None:
        global chart
        cursor.execute(
            "SELECT stock_code, SUM(order_quantity) FROM orders GROUP BY stock_code"
        )
        data = cursor.fetchall()
        x = []
        y = []
        for row in data:
            x.append(row[0])
            y.append(row[1])
        fig, ax = plt.subplots()
        ax.bar(x, y, color="#00677f")
        ax.set_xlabel("Stock Code")
        ax.set_ylabel("Order Quantity")
        ax.set_title("Stock Code vs Order Quantity")
        ax.set_facecolor("#fbfcfe")
        ax.tick_params(axis="x", colors="#191c1d")
        ax.tick_params(axis="y", colors="#191c1d")
        ax.spines["bottom"].set_color("#dbe4e8")
        ax.spines["top"].set_color("#dbe4e8")
        ax.spines["left"].set_color("#dbe4e8")
        ax.spines["right"].set_color("#dbe4e8")
        ax.xaxis.label.set_color("#191c1d")
        ax.yaxis.label.set_color("#191c1d")
        ax.title.set_color("#191c1d")
        chart = matplotlib_chart.MatplotlibChart(fig, transparent=True)
        page.route = "/chart"
        route_change(_)

    def back_to_route(_) -> None:
        global chart
        chart = None
        page.route = "/"
        route_change(_)

    def search(_) -> None:
        query = str(search_bar.value.strip())
        if query != "":
            search_stock_levels_table.visible = True
            stock_levels_table.visible = False
            columns_to_search = [column for column in stock_levels_columns]
            conditions = [
                f"CAST({column} as TEXT) LIKE %s" for column in columns_to_search
            ]
            where_clause = " OR ".join(conditions)
            sql_query = f"SELECT d.*, stocklevels.quantity, stocklevels.moq, stocklevels.on_order,\
                        stockbalance.balance FROM products d INNER JOIN stocklevels using(stock_code) INNER JOIN\
                        stockbalance using(stock_id) WHERE {where_clause}"
            params = [f"%{query}%"] * len(columns_to_search)
            cursor.execute(sql_query, params)
            search_data = cursor.fetchall()
            rows = []
            for row in search_data:
                rows.append(
                    DataRow(
                        cells=[DataCell(Text(str(cell))) for cell in row],
                        on_select_changed=lambda _, selected_row=row: load_data(
                            selected_row
                        ),
                    )
                )
                search_stock_levels_table.rows = rows
            page.update()
        else:
            search_stock_levels_table.rows = []
            search_stock_levels_table.visible = False
            stock_levels_table.visible = True
            page.update()

    def minimise_forms(_) -> None:
        if forms.visible:
            forms.visible = False
            minimise.icon = icons.ADD_ROUNDED
            page.update()
        else:
            forms.visible = True
            minimise.icon = icons.REMOVE_ROUNDED
            page.update()

    def clear_product_form(_) -> None:
        stock_code_product_tf.value = ""
        stock_cat_tf.value = ""
        description_tf.value = ""
        quantity_tf.value = ""
        moq_tf.value = ""
        page.update()

    def clear_order_form(_) -> None:
        stock_code_order_tf.value = ""
        order_quantity_tf.value = ""
        name_tf.value = ""
        address_tf.value = ""
        page.update()

    def obtain_stock_id(stock_code) -> int:
        cursor.execute(
            "SELECT stock_id FROM stocklevels WHERE stock_code = %s",
            (stock_code,),
        )
        return int(cursor.fetchone()[0])

    # obtains the quantity of a given stock code
    def obtain_quantity(stock_code) -> int:
        cursor.execute(
            "SELECT quantity FROM stocklevels WHERE stock_code = %s",
            (stock_code,),
        )
        return int(cursor.fetchone()[0])

    def obtain_moq(stock_code) -> int:
        cursor.execute(
            "SELECT moq FROM stocklevels WHERE stock_code = %s",
            (stock_code,),
        )
        return int(cursor.fetchone()[0])

    def obtain_on_order(stock_code) -> int:
        cursor.execute(
            "SELECT on_order FROM stocklevels WHERE stock_code = %s",
            (stock_code,),
        )
        return int(cursor.fetchone()[0])

    def check_value(value) -> str | int | None:
        return value if value != "" else None

    def refresh_page(_) -> None:
        clear_product_form(_)
        clear_order_form(_)
        refresh_table()
        if search_stock_levels_table.visible:
            search(_)
        page.update()

    def add_product_data(e) -> None:
        stock_code = check_value(str(stock_code_product_tf.value))
        stock_cat = check_value(int(stock_cat_tf.value))
        description = check_value(str(description_tf.value))
        quantity = check_value(int(quantity_tf.value))
        moq = check_value(int(moq_tf.value))
        if stock_code is not None:
            cursor.execute(
                "SELECT * FROM products WHERE stock_code = %s", (stock_code,)
            )
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
                stock_id = obtain_stock_id(stock_code)
                quantity = obtain_quantity(stock_code)
                on_order = obtain_on_order(stock_code)
                moq = obtain_moq(stock_code)
                cursor.execute(
                    "UPDATE stockbalance SET balance = %s WHERE stock_id = %s",
                    (quantity + moq - on_order, stock_id),
                )
                connection.commit()
            else:
                if None in [stock_cat or description or quantity or moq]:
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
                    stock_id = obtain_stock_id(stock_code)
                    cursor.execute(
                        "INSERT INTO stockbalance(stock_id, balance) VALUES(%s, %s)",
                        (stock_id, quantity + moq),
                    )
                    connection.commit()
        elif stock_code is None:
            show_banner("Please fill in the stock code field")
        refresh_page(_)

    def add_order_data(e) -> None:
        stock_code = check_value(str(stock_code_order_tf.value))
        quantity = check_value(int(order_quantity_tf.value))
        name = check_value(str(name_tf.value))
        address = check_value(str(address_tf.value))
        cursor.execute("SELECT * FROM products WHERE stock_code = %s", (stock_code,))
        if cursor.rowcount > 0:
            cursor.execute("SELECT * FROM customers WHERE name = %s", (name,))
            if cursor.rowcount == 0:
                if None in [stock_code or quantity or name or address]:
                    show_banner("Please fill in all fields")
                else:
                    cursor.execute(
                        "INSERT INTO customers(name, address) VALUES(%s, %s)",
                        (name, address),
                    )
                    connection.commit()
            if None in [stock_code or quantity or name]:
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
                on_order = obtain_on_order(stock_code)
                cursor.execute(
                    "UPDATE stocklevels SET on_order = %s WHERE stock_code = %s",
                    (on_order + quantity, stock_code),
                )
                connection.commit()
                on_order = on_order + quantity
                quantity = obtain_quantity(stock_code)
                moq = obtain_moq(stock_code)
                stock_id = obtain_stock_id(stock_code)
                cursor.execute(
                    "UPDATE stockbalance SET balance = %s WHERE stock_id = %s",
                    (quantity + moq - on_order, stock_id),
                )
                connection.commit()
        else:
            show_banner("Stock Code does not exist")
        refresh_page(_)

    def remove_product_data(e) -> None:
        stock_code = str(stock_code_product_tf.value)
        if stock_code != "":
            cursor.execute(
                "SELECT * FROM products WHERE stock_code = %s", (stock_code,)
            )
            if cursor.rowcount > 0:
                stock_id = obtain_stock_id(stock_code)
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
        else:
            show_banner("Please fill in the stock code field")
        refresh_page(_)

    def remove_order_data(e) -> None:
        order_id = check_value(int(order_id_tf.value))
        if order_id is not None:
            cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
            if cursor.rowcount > 0:
                cursor.execute(
                    "SELECT stock_code FROM orders WHERE order_id = %s", (order_id,)
                )
                stock_code = str(cursor.fetchone()[0])
                on_order = obtain_on_order(stock_code)
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
                quantity = obtain_quantity(stock_code)
                moq = obtain_moq(stock_code)
                stock_id = obtain_stock_id(stock_code)
                cursor.execute(
                    "UPDATE stockbalance SET balance = %s WHERE stock_id = %s",
                    (quantity + moq - on_order, stock_id),
                )
                connection.commit()
                cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
                connection.commit()
            else:
                show_banner("Order ID does not exist")
        else:
            show_banner("Please fill in the order ID field")
        refresh_page(_)

    sem = threading.Semaphore()

    page.window_min_width = 400
    page.window_min_height = 325
    page.theme = Theme(
        use_material3=True,
        color_scheme=ColorScheme(
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
    page.theme_mode = ThemeMode.LIGHT
    page.bgcolor = colors.BACKGROUND
    page.banner = Banner(
        bgcolor=colors.ERROR_CONTAINER,
        leading=Icon(icons.WARNING_AMBER_ROUNDED, color=colors.ON_ERROR_CONTAINER),
        actions=[
            IconButton(
                icon=icons.CLOSE,
                style=ButtonStyle(
                    color={
                        MaterialState.DEFAULT: colors.ON_ERROR_CONTAINER,
                    },
                    shape={MaterialState.DEFAULT: RoundedRectangleBorder(radius=8)},
                ),
                on_click=close_banner,
            )
        ],
    )

    search_icon = Icon(name=icons.SEARCH, color=colors.ON_PRIMARY, visible=False)

    search_bar = FormField(
        "Search",
        colors.ON_PRIMARY,
        colors.ON_PRIMARY,
        search,
        False,
    )

    stock_levels_table = Table(True)

    stock_levels_columns, _ = refresh_table()

    stock_levels_table.columns = [
        DataColumn(Text(str(column).capitalize().replace("_", " ")))
        for column in stock_levels_columns
    ]

    search_stock_levels_table = Table(False)

    search_stock_levels_table.columns = [
        DataColumn(Text(str(column).capitalize().replace("_", " ")))
        for column in stock_levels_columns
    ]

    stock_code_product_tf = FormField(
        "Stock Code",
        colors.SURFACE_VARIANT,
        colors.ON_SURFACE_VARIANT,
        None,
        True,
    )

    stock_code_order_tf = FormField(
        "Stock Code",
        colors.SURFACE_VARIANT,
        colors.ON_SURFACE_VARIANT,
        None,
        True,
    )

    order_id_tf = FormField(
        "Order ID",
        colors.SURFACE_VARIANT,
        colors.ON_SURFACE_VARIANT,
        None,
        True,
    )

    stock_cat_tf = FormField(
        "Stock Category",
        colors.SURFACE_VARIANT,
        colors.ON_SURFACE_VARIANT,
        None,
        True,
    )

    description_tf = FormField(
        "Description",
        colors.SURFACE_VARIANT,
        colors.ON_SURFACE_VARIANT,
        None,
        True,
    )

    quantity_tf = FormField(
        "Quantity",
        colors.SURFACE_VARIANT,
        colors.ON_SURFACE_VARIANT,
        None,
        True,
    )

    moq_tf = FormField(
        "MOQ",
        colors.SURFACE_VARIANT,
        colors.ON_SURFACE_VARIANT,
        None,
        True,
    )

    order_quantity_tf = FormField(
        "Order Quantity",
        colors.SURFACE_VARIANT,
        colors.ON_SURFACE_VARIANT,
        None,
        True,
    )

    name_tf = FormField(
        "Customer Name",
        colors.SURFACE_VARIANT,
        colors.ON_SURFACE_VARIANT,
        None,
        True,
    )

    address_tf = FormField(
        "Customer Address",
        colors.SURFACE_VARIANT,
        colors.ON_SURFACE_VARIANT,
        None,
        True,
    )

    add_product_button = Container(
        FormButton(icons.ADD_ROUNDED, add_product_data, colors.ON_PRIMARY, True),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    add_order_button = Container(
        FormButton(icons.ADD_ROUNDED, add_order_data, colors.ON_PRIMARY, True),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    delete_product_button = Container(
        FormButton(icons.DELETE_ROUNDED, remove_product_data, colors.ON_PRIMARY, True),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    delete_order_button = Container(
        FormButton(icons.DELETE_ROUNDED, remove_order_data, colors.ON_PRIMARY, True),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    clear_product_form_button = Container(
        FormButton(icons.CLEAR_ROUNDED, clear_product_form, colors.ON_PRIMARY, True),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    clear_order_form_button = Container(
        FormButton(icons.CLEAR_ROUNDED, clear_order_form, colors.ON_PRIMARY, True),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    display_product_chart_button = Container(
        FormButton(
            icons.INSIGHTS_ROUNDED,
            display_product_chart,
            colors.ON_PRIMARY,
            True,
        ),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    display_order_chart_button = Container(
        FormButton(
            icons.INSIGHTS_ROUNDED,
            display_order_chart,
            colors.ON_PRIMARY,
            True,
        ),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    back_button = FormButton(icons.ARROW_BACK, back_to_route, colors.PRIMARY, True)

    minimise = FormButton(icons.REMOVE_ROUNDED, minimise_forms, colors.ON_PRIMARY, True)

    forms = Container(
        Row(
            [
                Container(
                    Column(
                        [
                            Row(
                                [
                                    Text(
                                        "Add / Edit Product",
                                        weight=FontWeight.BOLD,
                                        color=colors.ON_BACKGROUND,
                                    ),
                                ]
                            ),
                            Row(
                                [
                                    stock_code_product_tf,
                                    add_product_button,
                                    delete_product_button,
                                    clear_product_form_button,
                                ]
                            ),
                            Row([description_tf]),
                            Row([stock_cat_tf]),
                            Row([quantity_tf, moq_tf, display_product_chart_button]),
                        ],
                        expand=True,
                        scroll=ScrollMode.AUTO,
                    ),
                    expand=True,
                    border=border.all(2, colors.SURFACE_VARIANT),
                    border_radius=8,
                    padding=15,
                    clip_behavior=ClipBehavior.HARD_EDGE,
                ),
                Container(
                    Column(
                        [
                            Text(
                                "Add Order",
                                weight=FontWeight.BOLD,
                                color=colors.ON_BACKGROUND,
                            ),
                            Row(
                                [
                                    order_id_tf,
                                    add_order_button,
                                    delete_order_button,
                                    clear_order_form_button,
                                ]
                            ),
                            Row([stock_code_order_tf, order_quantity_tf]),
                            Row([name_tf]),
                            Row([address_tf, display_order_chart_button]),
                        ],
                        expand=True,
                        scroll=ScrollMode.AUTO,
                    ),
                    expand=True,
                    border=border.all(2, colors.SURFACE_VARIANT),
                    border_radius=8,
                    padding=15,
                    clip_behavior=ClipBehavior.HARD_EDGE,
                ),
            ]
        ),
    )

    username_tf = LoginField("Username", False, None)

    password_tf = LoginField("Password", True, login)

    login_button = Container(
        FormButton(icons.LOGIN, login, colors.ON_PRIMARY, True),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    logout_button = Container(
        FormButton(icons.LOGOUT, logout, colors.ON_PRIMARY, True),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    login_form = Container(
        Column(
            [
                Text(
                    "Login",
                    weight=FontWeight.BOLD,
                    color=colors.ON_BACKGROUND,
                ),
                Row([username_tf]),
                Row([password_tf, login_button]),
            ],
            scroll=ScrollMode.AUTO,
        ),
        border=border.all(2, colors.SURFACE_VARIANT),
        border_radius=8,
        padding=15,
        clip_behavior=ClipBehavior.HARD_EDGE,
    )

    user_icon = Icon(
        name=icons.PERSON,
        color=colors.ON_PRIMARY,
        visible=False,
    )

    user_details = Container(
        border=border.all(2, colors.ON_PRIMARY),
        padding=Padding(left=10, right=2, top=2, bottom=2),
        border_radius=8,
        visible=False,
    )

    app_bar = Container(
        Row(
            [
                Container(
                    Text(
                        "Calibre Data Manager",
                        color=colors.ON_PRIMARY,
                        weight=FontWeight.BOLD,
                    ),
                    padding=10,
                ),
                search_icon,
                search_bar,
                user_icon,
                user_details,
                minimise,
            ],
            alignment=MainAxisAlignment.CENTER,
        ),
        padding=10,
        bgcolor=colors.PRIMARY,
        border_radius=border_radius.only(top_left=8, top_right=8),
        height=75,
    )

    def route_change(_) -> None:
        page.views.clear()
        page.window_width = 400
        page.window_height = 325
        page.window_resizable = True
        page.window_maximizable = False
        page.window_resizable = False
        search_icon.visible = False
        search_bar.visible = False
        user_icon.visible = False
        user_details.visible = False
        minimise.visible = False
        page.views.append(View("/login", [app_bar, login_form], padding=15))
        if page.route == "/" and admin:
            page.window_width = 800
            page.window_height = 700
            page.window_resizable = True
            page.window_maximizable = True
            search_icon.visible = True
            search_bar.visible = True
            user_icon.visible = True
            user_details.visible = True
            minimise.visible = True
            page.views.append(
                View(
                    "/",
                    [
                        app_bar,
                        forms,
                        Column(
                            [
                                Container(
                                    stock_levels_table,
                                    clip_behavior=ClipBehavior.HARD_EDGE,
                                ),
                                Container(
                                    search_stock_levels_table,
                                    clip_behavior=ClipBehavior.HARD_EDGE,
                                ),
                            ],
                            scroll=ScrollMode.AUTO,
                            on_scroll=on_scroll,
                            expand=True,
                        ),
                    ],
                    padding=15,
                )
            )
        elif page.route == "/chart" and admin:
            page.window_width = 700
            page.window_height = 700
            page.window_resizable = True
            page.window_maximizable = True
            page.views.append(
                View("/chart", [app_bar, Container(chart), back_button], padding=15)
            )
        else:
            page.route = "/login"
        page.update()

    page.on_route_change = route_change
    page.go(page.route)


if __name__ == "__main__":
    app(target=main)

cursor.close()
connection.close()
