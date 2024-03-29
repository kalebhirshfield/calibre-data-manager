from flet import TextStyle, TextField, DataTable, ButtonStyle, InputFilter
from flet import RoundedRectangleBorder, MaterialState, FontWeight
from flet import IconButton, icons, colors, border, Dropdown, dropdown


class SearchField(TextField):
    def __init__(self, on_change, visible: bool) -> None:
        super().__init__()
        self.label = "Search"
        self.label_style = TextStyle(color=colors.ON_PRIMARY, weight=FontWeight.W_600)
        self.text_style = TextStyle(color=colors.ON_PRIMARY, weight=FontWeight.W_600)
        self.expand = True
        self.border_radius = 8
        self.border_width = 2
        self.border_color = colors.ON_PRIMARY
        self.cursor_color = colors.ON_PRIMARY
        self.content_padding = 10
        self.on_submit = on_change
        self.visible = visible


class FormField(TextField):
    def __init__(self, label: str, visible: bool, type: type) -> None:
        super().__init__()
        self.label = label
        self.label_style = TextStyle(
            color=colors.ON_SURFACE_VARIANT, weight=FontWeight.W_600
        )
        self.text_style = TextStyle(
            color=colors.ON_SURFACE_VARIANT, weight=FontWeight.W_600
        )
        self.expand = True
        self.input_filter = InputFilter(
            allow=True, regex_string=r"[0-9]" if type == int else r"[^]"
        )
        self.border_radius = 8
        self.border_width = 2
        self.border_color = colors.SURFACE_VARIANT
        self.cursor_color = colors.ON_SURFACE_VARIANT
        self.content_padding = 10
        self.visible = visible


class LoginField(TextField):
    def __init__(self, label: str, password: bool, login) -> None:
        super().__init__()
        self.label = label
        self.label_style = TextStyle(
            color=colors.ON_SURFACE_VARIANT, weight=FontWeight.W_600
        )
        self.text_style = TextStyle(
            color=colors.ON_SURFACE_VARIANT, weight=FontWeight.W_600
        )
        self.expand = True
        self.border_radius = 8
        self.border_width = 2
        self.border_color = colors.SURFACE_VARIANT
        self.cursor_color = colors.ON_SURFACE_VARIANT
        self.content_padding = 10
        self.password = password
        self.can_reveal_password = password
        self.on_submit = login


class Table(DataTable):
    def __init__(self, visible: bool) -> None:
        super().__init__()
        self.border = border.all(2, colors.SURFACE_VARIANT)
        self.border_radius = 8
        self.divider_thickness = 0
        self.heading_row_height = 75
        self.horizontal_lines = border.BorderSide(1, colors.SURFACE_VARIANT)
        self.heading_text_style = TextStyle(
            color=colors.ON_BACKGROUND, weight=FontWeight.BOLD
        )
        self.data_text_style = TextStyle(
            color=colors.ON_SURFACE_VARIANT, weight=FontWeight.W_600
        )
        self.data_row_max_height = 75
        self.data_row_color = {
            MaterialState.HOVERED: colors.SURFACE_VARIANT,
            MaterialState.PRESSED: colors.SURFACE_VARIANT,
        }
        self.width = 10000
        self.visible = visible


class FormButton(IconButton):
    def __init__(self, icon: icons, click, color: colors, visible: bool) -> None:
        super().__init__()
        self.icon = icon
        self.style = ButtonStyle(
            color={MaterialState.DEFAULT: color},
            shape={MaterialState.DEFAULT: RoundedRectangleBorder(radius=8)},
        )
        self.on_click = click
        self.visible = visible


class Selection(Dropdown):
    def __init__(self, label, on_change) -> None:
        super().__init__()
        self.label = label
        self.label_style = TextStyle(color=colors.ON_BACKGROUND, weight=FontWeight.BOLD)
        self.options = [
            dropdown.Option("Product"),
            dropdown.Option("Order"),
            dropdown.Option("Customer"),
        ]
        self.value = "Product"
        self.content_padding = 10
        self.text_style = TextStyle(
            color=colors.ON_SURFACE_VARIANT, weight=FontWeight.W_600
        )
        self.border_color = colors.SURFACE_VARIANT
        self.border_width = 2
        self.border_radius = 8
        self.expand = True
        self.on_change = on_change
