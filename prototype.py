import os
import psycopg
from dotenv import load_dotenv
import flet as ft
from flet import RoundedRectangleBorder
import matplotlib
import matplotlib.pyplot as plt
from flet.matplotlib_chart import MatplotlibChart
from datetime import date

matplotlib.use("svg")

load_dotenv()
connection = psycopg.connect(os.getenv("DATABASE_URL"))
cursor = connection.cursor()


def main(page: ft.Page):
    def fetchStockLevels():
        global offset
        cursor.execute(
            "SELECT * FROM products d INNER JOIN stock_levels using(code) INNER JOIN stock_balance using(stock_id)"
        )
        stockLevels = cursor.fetchall()
        columnNames = [desc[0] for desc in cursor.description]
        rows = []
        for row in stockLevels:
            rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(cell)) for cell in row]))
        stockLevelsTable.rows = rows
        page.update()
        return columnNames

    def refreshTable(e):
        stockLevelsTable.rows = []
        fetchStockLevels()

    def showBanner(e, content):
        page.banner.open = True
        page.banner.content = ft.Text(content)
        page.update()

    def closeBanner(e):
        page.banner.open = False
        page.update()

    def tabSwitch(e):
        searchBar.visible = True if tabs.selected_index == 0 else False
        searchBar.label = (
            "Enter Stock Code to Display" if tabs.selected_index == 1 else "Search"
        )
        if tabs.selected_index == 1:
            search(e)
        page.update()

    def search(e):
        if tabs.selected_index == 0:
            query = str(searchBar.value.strip())
            if query != "":
                searchStockLevelsTable.visible = True
                stockLevelsTable.visible = False
                columnsToSearch = [column for column in stockLevelsColumns]
                conditions = [
                    f"CAST({column} as TEXT) LIKE %s" for column in columnsToSearch
                ]
                whereClause = " OR ".join(conditions)
                table = "products d INNER JOIN stock_levels using(code) INNER JOIN stock_balance using(stock_id)"
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
                    searchStockLevelsTable.rows = rows
                page.update()
            else:
                searchStockLevelsTable.rows = []
                searchStockLevelsTable.visible = False
                stockLevelsTable.visible = True
                page.update()
        elif tabs.selected_index == 1:
            searchBar.visible = False
            fig, ax = plt.subplots()
            cursor.execute(
                "SELECT category, SUM(quantity) FROM products INNER JOIN stock_levels using(code) GROUP BY category"
            )
            data = cursor.fetchall()
            x = []
            y = []
            for row in data:
                x.append(row[0])
                y.append(row[1])
            ax.set_xlabel("Stock Category")
            ax.set_ylabel("Quantity")
            ax.set_title("Stock Category vs Quantity")
            ax.bar(x, y, color="#00677f")
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
            tabs.tabs[1].content = ft.Container(chart, expand=True)
            page.update()

    def checkCustomerExists(e):
        if tabs.selected_index == 3:
            name = str(nameTF.value)
            cursor.execute("SELECT * FROM customers WHERE name = %s", (name,))
            if cursor.rowcount > 0:
                addressTF.visible = False
                addressTF.value = ""
                page.update()
            else:
                addressTF.visible = True
                page.update()

    def addNewData(e):
        if tabs.selected_index == 2:
            stockCode = (
                str(stockCodeTF.value.strip().upper())
                if stockCodeTF.value != ""
                else None
            )
            stockCAT = int(stockCATTF.value) if stockCATTF.value != "" else None
            description = (
                str(descriptionTF.value) if descriptionTF.value != "" else None
            )
            quantity = int(quantityTF.value) if quantityTF.value != "" else None
            moq = int(moqTF.value) if moqTF.value != "" else None
            if stockCode != None:
                cursor.execute("SELECT * FROM products WHERE code = %s", (stockCode,))
                if cursor.rowcount > 0:
                    cursor.execute(
                        "UPDATE products SET category = %s WHERE code = %s",
                        (stockCAT, stockCode),
                    ) if stockCAT != None else None
                    connection.commit()
                    cursor.execute(
                        "UPDATE products SET description = %s WHERE code = %s",
                        (description, stockCode),
                    ) if description != None else None
                    connection.commit()
                    cursor.execute(
                        "UPDATE stock_levels SET quantity = %s WHERE code = %s",
                        (quantity, stockCode),
                    ) if quantity != None else None
                    connection.commit()
                    cursor.execute(
                        "UPDATE stock_levels SET moq = %s WHERE code = %s",
                        (moq, stockCode),
                    ) if moq != None else None
                    connection.commit()
                    cursor.execute(
                        "Select stock_id FROM stock_levels WHERE code = %s",
                        (stockCode,),
                    )
                    stockID = int(cursor.fetchone()[0])
                    cursor.execute(
                        "SELECT quantity FROM stock_levels WHERE code = %s",
                        (stockCode,),
                    )
                    quantity = int(cursor.fetchone()[0])
                    cursor.execute(
                        "SELECT on_order FROM stock_levels WHERE code = %s",
                        (stockCode,),
                    )
                    onOrder = int(cursor.fetchone()[0])
                    cursor.execute(
                        "SELECT moq FROM stock_levels WHERE code = %s",
                        (stockCode,),
                    )
                    moq = int(cursor.fetchone()[0])
                    cursor.execute(
                        "UPDATE stock_balance SET balance = %s WHERE stock_id = %s",
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
                            "INSERT INTO products(code, category, description) VALUES(%s, %s, %s)",
                            (stockCode, stockCAT, description),
                        )
                        connection.commit()
                        cursor.execute(
                            "INSERT INTO stock_levels(code, moq, quantity) VALUES(%s, %s, %s)",
                            (stockCode, moq, quantity),
                        )
                        connection.commit()
                        cursor.execute(
                            "Select stock_id FROM stock_levels WHERE code = %s",
                            (stockCode,),
                        )
                        stockID = int(cursor.fetchone()[0])
                        cursor.execute(
                            "SELECT on_order FROM stock_levels WHERE code = %s",
                            (stockCode,),
                        )
                        onOrder = int(cursor.fetchone()[0])
                        cursor.execute(
                            "INSERT INTO stock_balance(stock_id, balance) VALUES(%s, %s)",
                            (stockID, quantity + moq - onOrder),
                        )
                        connection.commit()
                    else:
                        showBanner(
                            e,
                            "Please fill in all fields as there is no stock code match",
                        )
                    page.update()
            elif stockCode == None:
                showBanner(e, "Please fill in the stock code field")
                page.update()
        elif tabs.selected_index == 3:
            stockCode = (
                str(stockCodeTF.value.strip().upper())
                if stockCodeTF.value != ""
                else None
            )
            quantity = (
                int(orderQuantityTF.value) if orderQuantityTF.value != "" else None
            )
            name = str(nameTF.value) if nameTF.value != "" else None
            address = str(addressTF.value) if addressTF.value != "" else None
            cursor.execute("SELECT * FROM products WHERE code = %s", (stockCode,))
            if cursor.rowcount > 0:
                cursor.execute("SELECT * FROM customers WHERE name = %s", (name,))
                if cursor.rowcount > 0:
                    if stockCode != None and quantity != None and name != None:
                        cursor.execute(
                            "SELECT customer_id FROM customers WHERE name = %s",
                            (name,),
                        )
                        customerID = int(cursor.fetchone()[0])
                        cursor.execute(
                            "INSERT INTO orders(code, order_quantity, date, customer_id) VALUES(%s, %s, %s,%s)",
                            (stockCode, quantity, date.today(), customerID),
                        )
                        connection.commit()
                        cursor.execute(
                            "SELECT on_order FROM stock_levels WHERE code = %s",
                            (stockCode,),
                        )
                        onOrder = int(cursor.fetchone()[0])
                        cursor.execute(
                            "UPDATE stock_levels SET on_order = %s WHERE code = %s",
                            (onOrder + quantity, stockCode),
                        )
                        connection.commit()
                        onOrder = onOrder + quantity
                        cursor.execute(
                            "SELECT quantity FROM stock_levels WHERE code = %s",
                            (stockCode,),
                        )
                        quantity = int(cursor.fetchone()[0])
                        cursor.execute(
                            "SELECT moq FROM stock_levels WHERE code = %s",
                            (stockCode,),
                        )
                        moq = int(cursor.fetchone()[0])
                        cursor.execute(
                            "Select stock_id FROM stock_levels WHERE code = %s",
                            (stockCode,),
                        )
                        stockID = int(cursor.fetchone()[0])
                        cursor.execute(
                            "UPDATE stock_balance SET balance = %s WHERE stock_id = %s",
                            (quantity + moq - onOrder, stockID),
                        )
                        connection.commit()
                    else:
                        showBanner(e, "Please fill in all fields")
                    page.update()
                else:
                    if (
                        stockCode != None
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
                        customerID = int(cursor.fetchone()[0])
                        cursor.execute(
                            "INSERT INTO orders(code, order_quantity, date, customer_id) VALUES(%s, %s, %s,%s)",
                            (stockCode, quantity, date.today(), customerID),
                        )
                        connection.commit()
                        cursor.execute(
                            "SELECT on_order FROM stock_levels WHERE code = %s",
                            (stockCode,),
                        )
                        onOrder = int(cursor.fetchone()[0])
                        cursor.execute(
                            "UPDATE stock_levels SET on_order = %s WHERE code = %s",
                            (onOrder + quantity, stockCode),
                        )
                        connection.commit()
                        onOrder = onOrder + quantity
                        cursor.execute(
                            "SELECT quantity FROM stock_levels WHERE code = %s",
                            (stockCode,),
                        )
                        quantity = int(cursor.fetchone()[0])
                        cursor.execute(
                            "SELECT moq FROM stock_levels WHERE code = %s",
                            (stockCode,),
                        )
                        moq = int(cursor.fetchone()[0])
                        cursor.execute(
                            "Select stock_id FROM stock_levels WHERE code = %s",
                            (stockCode,),
                        )
                        stockID = int(cursor.fetchone()[0])
                        cursor.execute(
                            "UPDATE stock_balance SET balance = %s WHERE stock_id = %s",
                            (quantity + moq - onOrder, stockID),
                        )
                        connection.commit()
                    else:
                        showBanner(e, "Please fill in all fields")
                    page.update()
            else:
                showBanner(e, "Stock Code does not exist")
                page.update()
        stockCodeTF.value = ""
        stockCATTF.value = ""
        descriptionTF.value = ""
        quantityTF.value = ""
        moqTF.value = ""
        orderQuantityTF.value = ""
        nameTF.value = ""
        addressTF.value = ""
        refreshTable(e)

    def removeData(e):
        if tabs.selected_index == 2:
            stock_code = str(stockCodeTF.value.strip().upper())
            if stock_code != "":
                cursor.execute("SELECT * FROM products WHERE code = %s", (stock_code,))
                if cursor.rowcount > 0:
                    cursor.execute(
                        "SELECT stock_id FROM stock_levels WHERE code = %s",
                        (stock_code,),
                    )
                    stock_id = int(cursor.fetchone()[0])
                    cursor.execute(
                        "DELETE FROM stock_balance WHERE stock_id = %s", (stock_id,)
                    )
                    connection.commit()
                    cursor.execute(
                        "DELETE FROM stock_levels WHERE code = %s", (stock_code,)
                    )
                    connection.commit()
                    cursor.execute("DELETE FROM orders WHERE code = %s", (stock_code,))
                    connection.commit()
                    cursor.execute(
                        "DELETE FROM products WHERE code = %s", (stock_code,)
                    )
                    connection.commit()
                else:
                    showBanner(e, "Stock Code does not exist")
                    page.update()
            else:
                showBanner(e, "Please fill in the stock code field")
                page.update()
        elif tabs.selected_index == 3:
            stock_code = str(stockCodeTF.value.strip().upper())
            if stock_code != "":
                cursor.execute("SELECT * FROM orders WHERE ode = %s", (stock_code,))
                if cursor.rowcount > 0:
                    cursor.execute("DELETE FROM orders WHERE code = %s", (stock_code,))
                    connection.commit()
                else:
                    showBanner(e, "Stock Code does not exist")
                    page.update()
            else:
                showBanner(e, "Please fill in the stock code field")
                page.update()
        refreshTable(e)

    page.title = "Calibre Data Manager"
    page.window_width = 1200
    page.window_height = 600
    page.bgcolor = "#191c1d"
    page.banner = ft.Banner(
        bgcolor="#1b2628",
        leading=ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="#d6ca00"),
        actions=[ft.TextButton("Close", on_click=closeBanner)],
    )

    searchBar = ft.TextField(
        label="Search",
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
        on_change=search,
    )

    stockLevelsTable = ft.DataTable(
        bgcolor="#1b2628",
        border_radius=10,
        divider_thickness=0,
        heading_row_height=75,
        horizontal_lines=ft.border.BorderSide(0, "#004f58"),
        heading_text_style=ft.TextStyle(color="#e1e3e3", weight=ft.FontWeight.BOLD),
        data_text_style=ft.TextStyle(color="#e1e3e3"),
    )

    stockLevelsColumns = fetchStockLevels()

    stockLevelsTable.columns = [
        ft.DataColumn(ft.Text(column)) for column in stockLevelsColumns
    ]

    searchStockLevelsTable = ft.DataTable(
        columns=[ft.DataColumn(ft.Text(column)) for column in stockLevelsColumns],
        bgcolor="#1b2628",
        border_radius=10,
        divider_thickness=0,
        heading_row_height=75,
        horizontal_lines=ft.border.BorderSide(0, "#004f58"),
        heading_text_style=ft.TextStyle(color="#e1e3e3", weight=ft.FontWeight.BOLD),
        data_text_style=ft.TextStyle(color="#e1e3e3"),
        visible=False,
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

    orderQuantityTF = ft.TextField(
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

    nameTF = ft.TextField(
        label="Enter Customer Name",
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
        on_change=checkCustomerExists,
    )

    addressTF = ft.TextField(
        label="Enter Customer Address",
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

    addButton = ft.IconButton(
        icon=ft.icons.ADD_ROUNDED,
        style=ft.ButtonStyle(
            color={
                ft.MaterialState.DEFAULT: "#e1e3e3",
                ft.MaterialState.HOVERED: "#d6ca00",
            },
            shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=10)},
        ),
        on_click=addNewData,
    )

    deleteButton = ft.IconButton(
        icon=ft.icons.DELETE_ROUNDED,
        style=ft.ButtonStyle(
            color={
                ft.MaterialState.DEFAULT: "#e1e3e3",
                ft.MaterialState.HOVERED: "#ba1a1a",
            },
            shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=10)},
        ),
        on_click=removeData,
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
                content=ft.Container(
                    ft.Column(
                        [
                            ft.Divider(color=ft.colors.BACKGROUND),
                            stockLevelsTable,
                            searchStockLevelsTable,
                        ],
                        scroll=True,
                        expand=True,
                    ),
                ),
            ),
            ft.Tab(text="View Sales Patterns", icon=ft.icons.LINE_AXIS_ROUNDED),
            ft.Tab(
                text="Add / Edit Product Data",
                icon=ft.icons.EDIT_ROUNDED,
                content=ft.Container(
                    ft.Column(
                        [
                            ft.Divider(color=ft.colors.BACKGROUND),
                            ft.Row([stockCodeTF, addButton, deleteButton]),
                            ft.Row([stockCATTF]),
                            ft.Row([descriptionTF]),
                            ft.Row([quantityTF]),
                            ft.Row([moqTF]),
                        ]
                    )
                ),
            ),
        ],
        expand=True,
        on_change=tabSwitch,
    )

    titleBar = ft.Row(
        [
            ft.Container(
                ft.Column([ft.Row([searchBar])]),
                bgcolor="#1b2628",
                expand=True,
                border_radius=10,
                padding=10,
            )
        ]
    )

    page.add(titleBar, tabs)


ft.app(target=main)

cursor.close()
connection.close()
