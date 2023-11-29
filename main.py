import os
import threading
from datetime import date

import matplotlib
import matplotlib.pyplot as plt
import psycopg

from dotenv import load_dotenv
from flet import ClipBehavior, MainAxisAlignment, MaterialState, Padding, WindowDragArea
from flet import Column, Row, Container, DataColumn, DataRow, DataCell, ScrollMode
from flet import FontWeight, IconButton, ButtonStyle, RoundedRectangleBorder
from flet import Page, View, Text, Icon, Theme, ThemeMode, Banner, Divider
from flet import icons, colors, border, app, border_radius, matplotlib_chart

from controls import SearchField, FormField, LoginField, Table, FormButton, Selection

matplotlib.use("svg")

load_dotenv()
connection = psycopg.connect(os.getenv("DATABASE_URL"))
cursor = connection.cursor()

offset = 0
current_row = 0
admin = False
chart = None


def main(page: Page) -> None:
    # Datatable Functions
    def fetch_data(limit) -> tuple | int:
        global offset
        if table_select.value == "Product":
            query = """
                SELECT products.*, stock_levels.quantity, stock_levels.moq, stock_levels.on_order, 
                stock_balance.balance FROM products INNER JOIN stock_levels using(code) INNER JOIN 
                stock_balance using(stock_id) LIMIT %s OFFSET %s
            """
        elif table_select.value == "Order":
            query = """
                SELECT orders.order_id, orders.code, customers.name, orders.order_quantity, orders.date FROM orders INNER JOIN customers using(customer_id) 
                LIMIT %s OFFSET %s
            """
        elif table_select.value == "Customer":
            query = "SELECT name, address FROM customers LIMIT %s OFFSET %s"
        cursor.execute(query, (limit, offset))
        data = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        offset += limit
        return column_names, data

    def add_data_to_table(table, fetch_function, limit, rows) -> None:
        _, data = fetch_function(limit)
        rows += [
            DataRow(
                cells=[DataCell(Text(cell)) for cell in row],
                on_select_changed=lambda e, row=row: load_data(row),
            )
            for row in data
        ]
        table.rows = rows
        page.update()

    def on_scroll(e) -> None:
        if e.pixels >= e.max_scroll_extent - 300:
            if sem.acquire(blocking=False):
                try:
                    add_data_to_table(data_table, fetch_data, 10, data_table.rows)
                finally:
                    sem.release()

    sem = threading.Semaphore()

    def refresh_table(_) -> tuple | int:
        data_table.rows = []
        data_table.columns = []
        global offset
        offset = 0
        add_data_to_table(data_table, fetch_data, 20, data_table.rows)
        data_columns, _ = fetch_data(1)
        data_table.columns = [
            DataColumn(Text(str(column).capitalize().replace("_", " ")))
            for column in data_columns
        ]
        search_data_table.columns = [
            DataColumn(Text(str(column).capitalize().replace("_", " ")))
            for column in data_columns
        ]
        page.update()
        return data_columns

    def search(_) -> None:
        query = str(search_bar.value.strip())
        search_data_table.rows = []
        if query != "":
            search_data_table.visible = True
            data_table.visible = False
            data_columns = refresh_table(None)
            conditions = [f"CAST({column} as TEXT) LIKE %s" for column in data_columns]
            where_clause = " OR ".join(conditions)
            if table_select.value == "Product":
                sql_query = f"""
                    SELECT products.*, stock_levels.quantity, stock_levels.moq, stock_levels.on_order, 
                    stock_balance.balance FROM products INNER JOIN stock_levels using(code) INNER JOIN 
                    stock_balance using(stock_id) WHERE {where_clause}
                """
            elif table_select.value == "Order":
                sql_query = f"""
                    SELECT orders.order_id, orders.code, customers.name, orders.order_quantity, orders.date 
                    FROM orders INNER JOIN customers using(customer_id) WHERE {where_clause}
                """
            elif table_select.value == "Customer":
                sql_query = f"SELECT name, address FROM customers WHERE {where_clause}"
            params = [f"%{query}%"] * len(data_columns)
            cursor.execute(sql_query, params)
            search_data = cursor.fetchall()
            rows = []
            for row in search_data:
                rows.append(
                    DataRow(
                        cells=[DataCell(Text(str(cell))) for cell in row],
                        on_select_changed=lambda e, row=row: load_data(row),
                    )
                )
                search_data_table.rows = rows
        else:
            search_data_table.visible = False
            data_table.visible = True
        page.update()

    def load_data(row) -> None:
        if table_select.value == "Product":
            code_product_tf.value = row[0]
            category_tf.value = row[1]
            description_tf.value = row[2]
            quantity_tf.value = row[3]
            moq_tf.value = row[4]
        elif table_select.value == "Order":
            order_id_tf.value = row[0]
            code_order_tf.value = row[1]
            name_tf.value = row[2]
            order_quantity_tf.value = row[3]
        elif table_select.value == "Customer":
            name_tf.value = row[0]
            address_tf.value = row[1]
        page.update()

    # Form Functions
    def login(e) -> None:
        username = str(username_tf.value)
        password = str(password_tf.value)
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
        username_tf.value = ""
        password_tf.value = ""
        page.update()

    def logout(_) -> None:
        refresh_page(_)
        global admin
        admin = False
        page.route = "/login"
        route_change(_)
        page.update()

    def change_form(_) -> None:
        if form_select.value == "Product":
            product_form.visible = True
            order_form.visible = False
            customer_form.visible = False
        elif form_select.value == "Order":
            product_form.visible = False
            order_form.visible = True
            customer_form.visible = False
        elif form_select.value == "Customer":
            product_form.visible = False
            order_form.visible = False
            customer_form.visible = True
        elif form_select.value == " ":
            product_form.visible = False
            order_form.visible = False
            customer_form.visible = False
        page.update()

    def clear_form(_) -> None:
        if form_select.value == "Product":
            code_product_tf.value = ""
            category_tf.value = ""
            description_tf.value = ""
            quantity_tf.value = ""
            moq_tf.value = ""
        elif form_select.value == "Order":
            order_id_tf.value = ""
            code_order_tf.value = ""
            order_quantity_tf.value = ""
            name_tf.value = ""
        elif form_select.value == "Customer":
            name_tf.value = ""
            address_tf.value = ""
        page.update()

    def obtain_stock_id(code) -> int:
        cursor.execute(
            "SELECT stock_id FROM stock_levels WHERE code = %s",
            (code,),
        )
        return int(cursor.fetchone()[0])

    def obtain_quantity(code) -> int:
        cursor.execute(
            "SELECT quantity FROM stock_levels WHERE code = %s",
            (code,),
        )
        return int(cursor.fetchone()[0])

    def obtain_moq(code) -> int:
        cursor.execute(
            "SELECT moq FROM stock_levels WHERE code = %s",
            (code,),
        )
        return int(cursor.fetchone()[0])

    def obtain_on_order(code) -> int:
        cursor.execute(
            "SELECT on_order FROM stock_levels WHERE code = %s",
            (code,),
        )
        return int(cursor.fetchone()[0])

    def try_commit(query, params) -> None:
        try:
            cursor.execute(query, params)
            connection.commit()
        except psycopg.Error:
            if str(params[0]).isalnum():
                show_banner("Invalid data entered")
            connection.rollback()

    def presence_check(query, params) -> bool:
        cursor.execute(query, params)
        if cursor.rowcount > 0:
            return True
        else:
            return False

    def int_check(value) -> str | int:
        try:
            return int(value)
        except ValueError:
            return str(value)

    def add_product_data(_) -> None:
        code = str(code_product_tf.value)
        category = int_check(category_tf.value)
        description = str(description_tf.value)
        quantity = int_check(quantity_tf.value)
        moq = int_check(moq_tf.value)
        if presence_check("SELECT * FROM products WHERE code = %s", (code,)):
            try_commit(
                "UPDATE products SET category = %s WHERE code = %s",
                (category, code),
            )
            if description != "":
                try_commit(
                    "UPDATE products SET description = %s WHERE code = %s",
                    (description, code),
                )
            try_commit(
                "UPDATE stock_levels SET quantity = %s WHERE code = %s",
                (quantity, code),
            )
            try_commit("UPDATE stock_levels SET moq = %s WHERE code = %s", (moq, code))
            stock_id = obtain_stock_id(code)
            quantity = obtain_quantity(code)
            on_order = obtain_on_order(code)
            moq = obtain_moq(code)
            try_commit(
                "UPDATE stock_balance SET balance = %s WHERE stock_id = %s",
                (quantity - moq + on_order, stock_id),
            )
        else:
            try:
                cursor.execute(
                    "INSERT INTO products(code, category, description) VALUES(%s, %s, %s)",
                    (code, category, description),
                )
                connection.commit()
                cursor.execute(
                    "INSERT INTO stock_levels(code, moq, quantity, on_order) VALUES(%s, %s, %s, %s)",
                    (code, moq, quantity, 0),
                )
                connection.commit()
                stock_id = obtain_stock_id(code)
                cursor.execute(
                    "INSERT INTO stock_balance(stock_id, balance) VALUES(%s, %s)",
                    (stock_id, quantity + moq),
                )
                connection.commit()
            except psycopg.Error:
                connection.rollback()
                show_banner(
                    "Please fill in all fields as there is no stock code match",
                )
        refresh_page(_)

    def add_order_data(_) -> None:
        code = str(code_order_tf.value)
        name = str(name_tf.value)
        if str(order_quantity_tf.value).isnumeric() and code != "":
            if int(order_quantity_tf.value) >= obtain_moq(code):
                quantity = int(order_quantity_tf.value)
            else:
                quantity = str(order_quantity_tf.value)
        else:
            quantity = str(order_quantity_tf.value)
        if (
            presence_check("SELECT code FROM products WHERE code = %s", (code,))
            and presence_check(
                "SELECT customer_id FROM customers WHERE name = %s", (name,)
            )
            and type(quantity) == int
        ):
            customer_id = int(cursor.fetchone()[0])
            try:
                cursor.execute(
                    "INSERT INTO orders(code, order_quantity, date, customer_id) VALUES(%s, %s, %s,%s)",
                    (code, quantity, date.today(), customer_id),
                )
                connection.commit()
                on_order = obtain_on_order(code)
                cursor.execute(
                    "UPDATE stock_levels SET on_order = %s WHERE code = %s",
                    (on_order + quantity, code),
                )
                connection.commit()
                on_order = on_order + quantity
                quantity = obtain_quantity(code)
                moq = obtain_moq(code)
                stock_id = obtain_stock_id(code)
                cursor.execute(
                    "UPDATE stock_balance SET balance = %s WHERE stock_id = %s",
                    (quantity - moq + on_order, stock_id),
                )
                connection.commit()
            except psycopg.Error:
                connection.rollback()
                show_banner("Invalid data entered")
        else:
            show_banner("Invalid data entry")
        refresh_page(_)

    def add_customer_data(_) -> None:
        name = str(name_tf.value)
        address = str(address_tf.value)
        if presence_check("SELECT * FROM customers WHERE name = %s", (name,)):
            try_commit(
                "UPDATE customers SET address = %s WHERE name = %s", (address, name)
            )
        else:
            try_commit(
                "INSERT INTO customers(name, address) VALUES(%s, %s)",
                (name, address),
            )
        refresh_page(_)

    def remove_product_data(_) -> None:
        code = str(code_product_tf.value)
        try_commit("DELETE FROM stock_balance WHERE code = %s", (code,))
        refresh_page(_)

    def remove_order_data(_) -> None:
        order_id = int_check(order_id_tf.value)
        if presence_check("SELECT * FROM orders WHERE order_id = %s", (order_id,)):
            cursor.execute("SELECT code FROM orders WHERE order_id = %s", (order_id,))
            code = str(cursor.fetchone()[0])
            on_order = obtain_on_order(code)
            cursor.execute(
                "SELECT order_quantity FROM orders WHERE order_id = %s", (order_id,)
            )
            order_quantity = int(cursor.fetchone()[0])
            cursor.execute(
                "UPDATE stock_levels SET on_order = %s WHERE code = %s",
                (on_order - order_quantity, code),
            )
            connection.commit()
            on_order = on_order - order_quantity
            quantity = obtain_quantity(code)
            moq = obtain_moq(code)
            stock_id = obtain_stock_id(code)
            cursor.execute(
                "UPDATE stock_balance SET balance = %s WHERE stock_id = %s",
                (quantity + moq - on_order, stock_id),
            )
            connection.commit()
            cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
            connection.commit()
        else:
            show_banner("Order ID does not exist")
        refresh_page(_)

    def remove_customer_data(_) -> None:
        name = str(name_tf.value)
        try_commit("DELETE FROM orders WHERE name = %s", (name,))
        refresh_page(_)

    # Page Functions
    def refresh_page(_) -> None:
        clear_form(_)
        refresh_table(_)
        if search_data_table.visible:
            search(_)
        page.update()

    def display_chart(_) -> None:
        global chart
        x = []
        y = []
        fig, ax = plt.subplots()
        if form_select.value == "Product":
            cursor.execute(
                "SELECT category, SUM(quantity) FROM products INNER JOIN stock_levels using(code) GROUP BY category"
            )
            ax.set_xlabel("Stock Category")
            ax.set_ylabel("Quantity")
            ax.set_title("Stock Category vs Quantity")
        else:
            cursor.execute("SELECT code, SUM(order_quantity) FROM orders GROUP BY code")
            ax.set_xlabel("Stock Code")
            ax.set_ylabel("Order Quantity")
            ax.set_title("Stock Code vs Order Quantity")
        data = cursor.fetchall()
        for row in data:
            x.append(row[0])
            y.append(row[1])
        ax.yaxis.grid(color="#dbe4e8")
        ax.bar(x, y, color="#00677f")
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

    def show_banner(content) -> None:
        page.banner.open = True
        page.banner.content = Text(content, color=colors.ON_ERROR_CONTAINER)
        page.update()

    def close_banner(_) -> None:
        page.banner.open = False
        page.update()

    def toggle_theme(_) -> None:
        if page.theme_mode == ThemeMode.LIGHT:
            page.theme_mode = ThemeMode.DARK
            theme_toggle_button.icon = icons.LIGHT_MODE_ROUNDED
        else:
            page.theme_mode = ThemeMode.LIGHT
            theme_toggle_button.icon = icons.DARK_MODE_ROUNDED
        page.update()

    # Page
    page.theme = Theme(use_material3=True, color_scheme_seed="cyan")
    page.theme_mode = ThemeMode.LIGHT
    page.window_title_bar_hidden = True
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

    search_bar = SearchField(search, False)

    data_table = Table(True)

    table_select = Selection("Select Table", refresh_page)

    search_data_table = Table(False)

    refresh_table(None)

    code_product_tf = FormField("Code", True, str)

    code_order_tf = FormField("Code", True, str)

    order_id_tf = FormField("Order ID", True, int)

    category_tf = FormField("Category", True, int)

    description_tf = FormField("Description", True, str)

    quantity_tf = FormField("Quantity", True, int)

    moq_tf = FormField("MOQ", True, int)

    order_quantity_tf = FormField("Order Quantity", True, int)

    name_tf = FormField("Name", True, str)

    address_tf = FormField("Address", True, str)

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

    add_customer_button = Container(
        FormButton(icons.ADD_ROUNDED, add_customer_data, colors.ON_PRIMARY, True),
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

    delete_customer_button = Container(
        FormButton(icons.DELETE_ROUNDED, remove_customer_data, colors.ON_PRIMARY, True),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    clear_form_button = Container(
        FormButton(icons.CLEAR_ROUNDED, clear_form, colors.ON_PRIMARY, True),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    display_product_chart_button = Container(
        FormButton(
            icons.INSIGHTS_ROUNDED,
            display_chart,
            colors.ON_PRIMARY,
            True,
        ),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    display_order_chart_button = Container(
        FormButton(
            icons.INSIGHTS_ROUNDED,
            display_chart,
            colors.ON_PRIMARY,
            True,
        ),
        bgcolor=colors.PRIMARY,
        border_radius=8,
    )

    back_button = FormButton(icons.ARROW_BACK, back_to_route, colors.PRIMARY, True)

    product_form = Container(
        Row(
            [
                Container(
                    Column(
                        [
                            Row(
                                [
                                    code_product_tf,
                                    category_tf,
                                    quantity_tf,
                                    moq_tf,
                                    add_product_button,
                                    delete_product_button,
                                ]
                            ),
                            Row(
                                [
                                    description_tf,
                                    clear_form_button,
                                    display_product_chart_button,
                                ]
                            ),
                        ],
                        expand=True,
                        scroll=ScrollMode.AUTO,
                    ),
                    expand=True,
                    clip_behavior=ClipBehavior.HARD_EDGE,
                    padding=Padding(left=0, right=0, top=15, bottom=15),
                ),
            ]
        ),
    )

    order_form = Container(
        Row(
            [
                Container(
                    Column(
                        [
                            Row(
                                [
                                    order_id_tf,
                                    code_order_tf,
                                    add_order_button,
                                    delete_order_button,
                                ]
                            ),
                            Row(
                                [
                                    name_tf,
                                    order_quantity_tf,
                                    clear_form_button,
                                    display_order_chart_button,
                                ]
                            ),
                        ],
                        expand=True,
                        scroll=ScrollMode.AUTO,
                    ),
                    expand=True,
                    padding=Padding(left=0, right=0, top=15, bottom=15),
                    clip_behavior=ClipBehavior.HARD_EDGE,
                ),
            ]
        ),
        visible=False,
    )

    customer_form = Container(
        Row(
            [
                Container(
                    Column(
                        [
                            Row(
                                [
                                    name_tf,
                                    add_customer_button,
                                    delete_customer_button,
                                    clear_form_button,
                                ]
                            ),
                            Row([address_tf]),
                        ],
                        expand=True,
                        scroll=ScrollMode.AUTO,
                    ),
                    expand=True,
                    padding=Padding(left=0, right=0, top=15, bottom=15),
                    clip_behavior=ClipBehavior.HARD_EDGE,
                ),
            ]
        ),
        visible=False,
    )

    form_select = Selection("Select Form", change_form)

    username_tf = LoginField("Username", False, login)

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
                Row([username_tf]),
                Row([password_tf, login_button]),
            ],
            scroll=ScrollMode.AUTO,
        ),
        padding=Padding(left=0, right=0, top=15, bottom=15),
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

    theme_toggle_button = FormButton(
        icons.DARK_MODE_ROUNDED, toggle_theme, colors.BACKGROUND, True
    )

    close_button = FormButton(
        icons.CLOSE, lambda _: page.window_close(), colors.BACKGROUND, True
    )

    app_bar = WindowDragArea(
        Container(
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
                    theme_toggle_button,
                    close_button,
                ],
                alignment=MainAxisAlignment.CENTER,
            ),
            padding=10,
            bgcolor=colors.PRIMARY,
            border_radius=border_radius.only(bottom_left=20, bottom_right=20),
            height=75,
        )
    )

    def route_change(_) -> None:
        page.views.clear()
        page.window_width = 400
        page.window_height = 300
        page.window_resizable = True
        page.window_maximizable = False
        page.window_resizable = False
        search_icon.visible = False
        search_bar.visible = False
        user_icon.visible = False
        user_details.visible = False
        page.views.append(
            View("/login", [app_bar, Container(login_form, padding=20)], padding=0)
        )
        if page.route == "/" and admin:
            page.window_width = 900
            page.window_height = 700
            page.window_resizable = True
            page.window_maximizable = True
            search_icon.visible = True
            search_bar.visible = True
            user_icon.visible = True
            user_details.visible = True
            page.views.append(
                View(
                    "/",
                    [
                        app_bar,
                        Container(
                            Column(
                                [
                                    Divider(color=colors.TRANSPARENT),
                                    Row([form_select, table_select]),
                                    product_form,
                                    order_form,
                                    customer_form,
                                    Column(
                                        [
                                            Container(
                                                data_table,
                                                clip_behavior=ClipBehavior.HARD_EDGE,
                                            ),
                                            Container(
                                                search_data_table,
                                                clip_behavior=ClipBehavior.HARD_EDGE,
                                            ),
                                        ],
                                    ),
                                ],
                                expand=True,
                            ),
                            padding=20,
                        ),
                    ],
                    padding=0,
                    scroll=ScrollMode.AUTO,
                    on_scroll=on_scroll,
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
