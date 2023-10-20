import os
import threading
import psycopg
from dotenv import load_dotenv
import flet as ft
from flet import RoundedRectangleBorder
from datetime import date

load_dotenv()
connection = psycopg.connect(os.getenv("dbURL"))
cursor = connection.cursor()

offset = 0


def main(page: ft.Page):
    def fetchStockLevels(limit):
        global offset
        cursor.execute(
            "SELECT * FROM products d INNER JOIN stocklevels using(stock_code) INNER JOIN stockbalance using(stock_id) LIMIT %s OFFSET %s",
            (limit, offset),
        )
        stockLevels = cursor.fetchall()
        columnNames = [desc[0] for desc in cursor.description]
        offset += limit
        return columnNames, stockLevels

    def addDataToTable(table: ft.DataTable, fetchFunction, limit, rows):
        columnNames, data = fetchFunction(limit=limit)
        newRows = []
        for row in data:
            newRows.append(
                ft.DataRow(cells=[ft.DataCell(ft.Text(cell)) for cell in row])
            )
        rows += newRows
        table.rows = rows
        page.update()

    def onScroll(e: ft.OnScrollEvent):
        if e.pixels >= e.max_scroll_extent - 300:
            if sem.acquire(blocking=False):
                try:
                    addDataToTable(
                        stockLevelsTable,
                        fetchStockLevels,
                        10,
                        stockLevelsTable.rows,
                    )
                finally:
                    sem.release()

    def refreshTable(e):
        stockLevelsTable.rows = []
        global offset
        offset = 0
        addDataToTable(stockLevelsTable, fetchStockLevels, 20, stockLevelsTable.rows)
        return fetchStockLevels(1)

    def showBanner(e, content):
        page.banner.open = True
        page.banner.content = ft.Text(content, color="#410002")
        page.update()

    def closeBanner(e):
        page.banner.open = False
        page.update()

    def search(e):
        query = str(searchBar.value.strip())
        if query != "":
            searchStockLevelsTable.visible = True
            stockLevelsTable.visible = False
            columnsToSearch = [column for column in stockLevelsColumns]
            conditions = [
                f"CAST({column} as TEXT) LIKE %s" for column in columnsToSearch
            ]
            whereClause = " OR ".join(conditions)
            table = "products d INNER JOIN stocklevels using(stock_code) INNER JOIN stockbalance using(stock_id)"
            sqlQuery = f"SELECT * FROM {table} WHERE {whereClause}"
            params = [f"%{query}%"] * len(columnsToSearch)
            cursor.execute(sqlQuery, params)
            searchData = cursor.fetchall()
            rows = []
            for row in searchData:
                rows.append(
                    ft.DataRow(cells=[ft.DataCell(ft.Text(str(cell))) for cell in row])
                )
                searchStockLevelsTable.rows = rows
            page.update()
        else:
            searchStockLevelsTable.rows = []
            searchStockLevelsTable.visible = False
            stockLevelsTable.visible = True
            page.update()

    def minimiseForms(e):
        if forms.visible == True:
            forms.visible = False
            minimise.icon = ft.icons.ADD_ROUNDED
            formPlaceholder.visible = True
            page.update()
        else:
            forms.visible = True
            minimise.icon = ft.icons.REMOVE_ROUNDED
            formPlaceholder.visible = False
            page.update()

    def checkCustomerExists(e):
        name = str(nameTF.value)
        cursor.execute("SELECT * FROM customers WHERE name = %s", (name,))
        if cursor.rowcount > 0:
            addressTF.visible = False
            addressTF.value = ""
            page.update()
        else:
            addressTF.visible = True
            page.update()

    def addProductData(e):
        stockCode = (
            str(stockCodeTF.value.strip().upper()) if stockCodeTF.value != "" else None
        )
        stockCAT = int(stockCATTF.value) if stockCATTF.value != "" else None
        description = str(descriptionTF.value) if descriptionTF.value != "" else None
        quantity = int(quantityTF.value) if quantityTF.value != "" else None
        moq = int(moqTF.value) if moqTF.value != "" else None
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
                        "INSERT INTO stocklevels(stock_code, moq, quantity) VALUES(%s, %s, %s)",
                        (stockCode, moq, quantity),
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
                    onOrder = int(cursor.fetchone()[0])
                    cursor.execute(
                        "INSERT INTO stockbalance(stock_id, balance) VALUES(%s, %s)",
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
        stockCodeTF.value = ""
        stockCATTF.value = ""
        descriptionTF.value = ""
        quantityTF.value = ""
        moqTF.value = ""
        refreshTable(e)

    def addOrderData(e):
        stockCode = (
            str(stockCodeTF.value.strip().upper()) if stockCodeTF.value != "" else None
        )
        quantity = int(orderQuantityTF.value) if orderQuantityTF.value != "" else None
        name = str(nameTF.value) if nameTF.value != "" else None
        address = str(addressTF.value) if addressTF.value != "" else None
        cursor.execute("SELECT * FROM products WHERE stock_code = %s", (stockCode,))
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
                        "INSERT INTO orders(stock_code, order_quantity, date, customer_id) VALUES(%s, %s, %s,%s)",
                        (stockCode, quantity, date.today(), customerID),
                    )
                    connection.commit()
                    cursor.execute(
                        "SELECT on_order FROM stocklevels WHERE stock_code = %s",
                        (stockCode,),
                    )
                    onOrder = int(cursor.fetchone()[0])
                    cursor.execute(
                        "UPDATE stocklevels SET on_order = %s WHERE stock_code = %s",
                        (onOrder + quantity, stockCode),
                    )
                    connection.commit()
                    onOrder = onOrder + quantity
                    cursor.execute(
                        "SELECT quantity FROM stocklevels WHERE stock_code = %s",
                        (stockCode,),
                    )
                    quantity = int(cursor.fetchone()[0])
                    cursor.execute(
                        "SELECT moq FROM stocklevels WHERE stock_code = %s",
                        (stockCode,),
                    )
                    moq = int(cursor.fetchone()[0])
                    cursor.execute(
                        "Select stock_id FROM stocklevels WHERE stock_code = %s",
                        (stockCode,),
                    )
                    stockID = int(cursor.fetchone()[0])
                    cursor.execute(
                        "UPDATE stockbalance SET balance = %s WHERE stock_id = %s",
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
                        "INSERT INTO orders(stock_code, order_quantity, date, customer_id) VALUES(%s, %s, %s,%s)",
                        (stockCode, quantity, date.today(), customerID),
                    )
                    connection.commit()
                    cursor.execute(
                        "SELECT on_order FROM stocklevels WHERE stock_code = %s",
                        (stockCode,),
                    )
                    onOrder = int(cursor.fetchone()[0])
                    cursor.execute(
                        "UPDATE stocklevels SET on_order = %s WHERE stock_code = %s",
                        (onOrder + quantity, stockCode),
                    )
                    connection.commit()
                    onOrder = onOrder + quantity
                    cursor.execute(
                        "SELECT quantity FROM stocklevels WHERE stock_code = %s",
                        (stockCode,),
                    )
                    quantity = int(cursor.fetchone()[0])
                    cursor.execute(
                        "SELECT moq FROM stocklevels WHERE stock_code = %s",
                        (stockCode,),
                    )
                    moq = int(cursor.fetchone()[0])
                    cursor.execute(
                        "Select stock_id FROM stocklevels WHERE stock_code = %s",
                        (stockCode,),
                    )
                    stockID = int(cursor.fetchone()[0])
                    cursor.execute(
                        "UPDATE stockbalance SET balance = %s WHERE stock_id = %s",
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
        orderQuantityTF.value = ""
        nameTF.value = ""
        addressTF.value = ""
        refreshTable(e)

    def removeProductData(e):
        stock_code = str(stockCodeTF.value.strip().upper())
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
                showBanner(e, "Stock Code does not exist")
                page.update()
        else:
            showBanner(e, "Please fill in the stock code field")
            page.update()
        stockCodeTF.value = ""
        stockCATTF.value = ""
        descriptionTF.value = ""
        quantityTF.value = ""
        moqTF.value = ""
        refreshTable(e)

    def removeOrderData(e):
        stock_code = str(stockCodeTF.value.strip().upper())
        if stock_code != "":
            cursor.execute("SELECT * FROM orders WHERE stock_code = %s", (stock_code,))
            if cursor.rowcount > 0:
                cursor.execute(
                    "DELETE FROM orders WHERE stock_code = %s", (stock_code,)
                )
                connection.commit()
            else:
                showBanner(e, "Stock Code does not exist")
                page.update()
        else:
            showBanner(e, "Please fill in the stock code field")
            page.update()
        stockCodeTF.value = ""
        orderQuantityTF.value = ""
        nameTF.value = ""
        addressTF.value = ""
        refreshTable(e)

    sem = threading.Semaphore()

    page.title = "Calibre Data Manager"
    page.window_width = 1200
    page.window_min_width = 1200
    page.window_height = 900
    page.window_min_height = 900
    page.window_title_bar_hidden = True
    page.window_title_bar_buttons_hidden = True
    page.window_resizable = False
    page.window_maximizable = False
    page.bgcolor = "#fafcff"
    page.banner = ft.Banner(
        bgcolor="#ffdad6",
        leading=ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="#410002"),
        actions=[
            ft.IconButton(
                icon=ft.icons.CLOSE,
                style=ft.ButtonStyle(
                    color={
                        ft.MaterialState.DEFAULT: "#410002",
                    },
                    shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=10)},
                ),
                on_click=closeBanner,
            )
        ],
    )

    windowDragArea = ft.WindowDragArea(
        ft.Container(
            ft.Text(
                "Calibre Data Manager",
                color="#ffffff",
                text_align="left",
                weight=ft.FontWeight.BOLD,
            ),
            padding=10,
        ),
        maximizable=False,
    )

    btnClose = ft.IconButton(
        ft.icons.CLOSE,
        style=ft.ButtonStyle(
            color={
                ft.MaterialState.DEFAULT: "#ffffff",
            },
            shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=10)},
        ),
        on_click=lambda _: page.window_close(),
    )

    searchBar = ft.TextField(
        hint_text="Search",
        hint_style=ft.TextStyle(color="#001f28"),
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#001f28"),
        label_style=ft.TextStyle(color="#e1e3e3", weight=ft.FontWeight.BOLD),
        border_color=ft.colors.TRANSPARENT,
        bgcolor="#b7eaff",
        cursor_color="#001f28",
        content_padding=10,
        on_change=search,
    )

    stockLevelsTable = ft.DataTable(
        border=ft.border.all(2, "#dbe4e8"),
        border_radius=10,
        divider_thickness=0,
        heading_row_height=75,
        horizontal_lines=ft.border.BorderSide(1, "#004f58"),
        heading_text_style=ft.TextStyle(color="#001f2a", weight=ft.FontWeight.BOLD),
        data_text_style=ft.TextStyle(color="#001f2a"),
        column_spacing=65,
    )

    stockLevelsColumns, _ = refreshTable(None)

    stockLevelsTable.columns = [
        ft.DataColumn(ft.Text(column)) for column in stockLevelsColumns
    ]

    searchStockLevelsTable = ft.DataTable(
        columns=[ft.DataColumn(ft.Text(column)) for column in stockLevelsColumns],
        border=ft.border.all(2, "#dbe4e8"),
        border_radius=10,
        divider_thickness=0,
        heading_row_height=75,
        horizontal_lines=ft.border.BorderSide(1, "#004f58"),
        heading_text_style=ft.TextStyle(color="#001f2a", weight=ft.FontWeight.BOLD),
        data_text_style=ft.TextStyle(color="#001f2a"),
        column_spacing=65,
        visible=False,
    )

    stockCodeTF = ft.TextField(
        hint_text="Stock Code",
        hint_style=ft.TextStyle(color="#40484c"),
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#40484c"),
        label_style=ft.TextStyle(color="#40484c"),
        border_width=2,
        focused_border_width=4,
        border_color=ft.colors.TRANSPARENT,
        bgcolor="#dbe4e8",
        cursor_color="#40484c",
    )

    stockCATTF = ft.TextField(
        hint_text="Stock CAT",
        hint_style=ft.TextStyle(color="#40484c"),
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#40484c"),
        label_style=ft.TextStyle(color="#40484c"),
        border_width=2,
        focused_border_width=4,
        border_color=ft.colors.TRANSPARENT,
        bgcolor="#dbe4e8",
        cursor_color="#40484c",
    )

    descriptionTF = ft.TextField(
        hint_text="Description",
        hint_style=ft.TextStyle(color="#40484c"),
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#40484c"),
        label_style=ft.TextStyle(color="#40484c"),
        border_width=2,
        focused_border_width=4,
        border_color=ft.colors.TRANSPARENT,
        bgcolor="#dbe4e8",
        cursor_color="#40484c",
    )

    quantityTF = ft.TextField(
        hint_text="Quantity",
        hint_style=ft.TextStyle(color="#40484c"),
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#40484c"),
        label_style=ft.TextStyle(color="#40484c"),
        border_width=2,
        focused_border_width=4,
        border_color=ft.colors.TRANSPARENT,
        bgcolor="#dbe4e8",
        cursor_color="#40484c",
    )

    moqTF = ft.TextField(
        hint_text="MOQ",
        hint_style=ft.TextStyle(color="#40484c"),
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#40484c"),
        label_style=ft.TextStyle(color="#40484c"),
        border_width=2,
        focused_border_width=4,
        border_color=ft.colors.TRANSPARENT,
        bgcolor="#dbe4e8",
        cursor_color="#40484c",
    )

    orderQuantityTF = ft.TextField(
        hint_text="Quantity",
        hint_style=ft.TextStyle(color="#40484c"),
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#40484c"),
        label_style=ft.TextStyle(color="#40484c"),
        border_width=2,
        focused_border_width=4,
        border_color=ft.colors.TRANSPARENT,
        bgcolor="#dbe4e8",
        cursor_color="#40484c",
    )

    nameTF = ft.TextField(
        hint_text="Customer Name",
        hint_style=ft.TextStyle(color="#40484c"),
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#40484c"),
        label_style=ft.TextStyle(color="#40484c"),
        border_width=2,
        focused_border_width=4,
        border_color=ft.colors.TRANSPARENT,
        bgcolor="#dbe4e8",
        cursor_color="#40484c",
        on_change=checkCustomerExists,
    )

    addressTF = ft.TextField(
        hint_text="Customer Address",
        hint_style=ft.TextStyle(color="#40484c"),
        expand=True,
        border_radius=10,
        text_style=ft.TextStyle(color="#40484c"),
        label_style=ft.TextStyle(color="#40484c"),
        border_width=2,
        focused_border_width=4,
        border_color=ft.colors.TRANSPARENT,
        bgcolor="#dbe4e8",
        cursor_color="#40484c",
    )

    addProductButton = ft.FloatingActionButton(
        icon=ft.icons.ADD_ROUNDED,
        bgcolor="#00677f",
        shape=RoundedRectangleBorder(radius=10),
        mini=True,
        on_click=addProductData,
    )

    addOrderButton = ft.FloatingActionButton(
        icon=ft.icons.ADD_ROUNDED,
        bgcolor="#00677f",
        shape=RoundedRectangleBorder(radius=10),
        mini=True,
        on_click=addOrderData,
    )

    deleteProductButton = ft.FloatingActionButton(
        icon=ft.icons.DELETE_ROUNDED,
        bgcolor="#00677f",
        shape=RoundedRectangleBorder(radius=10),
        mini=True,
        on_click=removeProductData,
    )

    deleteOrderButton = ft.FloatingActionButton(
        icon=ft.icons.DELETE_ROUNDED,
        bgcolor="#00677f",
        shape=RoundedRectangleBorder(radius=10),
        mini=True,
        on_click=removeOrderData,
    )

    minimise = ft.IconButton(
        ft.icons.REMOVE_ROUNDED,
        style=ft.ButtonStyle(
            color={
                ft.MaterialState.DEFAULT: "#00677f",
            },
            shape={ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=10)},
        ),
        on_click=minimiseForms,
    )

    bar = ft.Container(
        ft.Row([windowDragArea, searchBar, btnClose]),
        padding=10,
        bgcolor="#00677f",
        expand=True,
        border_radius=10,
    )

    forms = ft.Container(
        ft.Row(
            [
                ft.Container(
                    ft.Column(
                        [
                            ft.Text(
                                "Add Product",
                                weight=ft.FontWeight.BOLD,
                                color="#001f2a",
                            ),
                            ft.Row(
                                [stockCodeTF, addProductButton, deleteProductButton]
                            ),
                            ft.Row([descriptionTF]),
                            ft.Row([stockCATTF]),
                            ft.Row([quantityTF, moqTF]),
                        ],
                        expand=True,
                        scroll=True,
                    ),
                    expand=True,
                    border=ft.border.all(2, "#dbe4e8"),
                    border_radius=10,
                    padding=15,
                    height=320,
                ),
                ft.Container(
                    ft.Column(
                        [
                            ft.Text(
                                "Add Order",
                                weight=ft.FontWeight.BOLD,
                                color="#001f2a",
                            ),
                            ft.Row([stockCodeTF, addOrderButton, deleteOrderButton]),
                            ft.Row([orderQuantityTF]),
                            ft.Row([nameTF]),
                            ft.Row([addressTF]),
                        ],
                        scroll=True,
                        expand=True,
                    ),
                    expand=True,
                    border=ft.border.all(2, "#dbe4e8"),
                    border_radius=10,
                    padding=15,
                    height=320,
                ),
            ]
        ),
        expand=True,
        alignment=ft.Alignment(0, -1),
    )

    formPlaceholder = ft.Container(
        ft.Column([ft.Divider(color="#dbe4e8")]), padding=10, visible=False
    )

    page.add(
        ft.Container(bar),
        forms,
        formPlaceholder,
        minimise,
        ft.Column(
            [
                stockLevelsTable,
                searchStockLevelsTable,
            ],
            scroll=True,
            on_scroll=onScroll,
            expand=True,
        ),
    )


if __name__ == "__main__":
    ft.app(target=main)

cursor.close()
connection.close()
