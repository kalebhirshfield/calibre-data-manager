import flet as ft
from flet import (
    TextStyle,
    TextField,
    DataTable,
    border,
    colors,
    FontWeight,
    MaterialState,
    IconButton,
    icons,
    ButtonStyle,
    RoundedRectangleBorder,
    Container,
)


class FormField(TextField):
    def __init__(
        self,
        hint_text: str,
        bordercolor: colors,
        bgcolor: colors,
        textcolor: colors,
        change,
        visible: bool,
    ) -> None:
        super().__init__()
        self.hint_text = hint_text
        self.hint_style = TextStyle(color=textcolor)
        self.text_style = TextStyle(color=textcolor, weight=FontWeight.W_600)
        self.expand = True
        self.border_radius = 8
        self.border_color = bordercolor
        self.border_width = 2
        self.bgcolor = bgcolor
        self.cursor_color = textcolor
        self.on_submit = change
        self.content_padding = 10
        self.visible = visible

    def build(self) -> TextField:
        return TextField(
            hint_text=self.hint_text,
            hint_style=self.hint_style,
            text_style=self.text_style,
            expand=self.expand,
            border_radius=self.border_radius,
            border_color=self.border_color,
            border_width=self.border_width,
            bgcolor=self.bgcolor,
            cursor_color=self.cursor_color,
            on_change=self.on_change,
            content_padding=self.content_padding,
            visible=self.visible,
        )


class LoginField(TextField):
    def __init__(self, hint_text: str, password: bool, click) -> None:
        super().__init__()
        self.hint_text = hint_text
        self.hint_style = TextStyle(color=colors.ON_SURFACE_VARIANT)
        self.text_style = TextStyle(
            color=colors.ON_SURFACE_VARIANT, weight=FontWeight.W_600
        )
        self.expand = True
        self.border_radius = 8
        self.border_color = colors.TRANSPARENT
        self.bgcolor = colors.SURFACE_VARIANT
        self.cursor_color = colors.ON_SURFACE_VARIANT
        self.content_padding = 10
        self.password = password
        self.can_reveal_password = password
        self.on_submit = click

    def build(self) -> TextField:
        return TextField(
            hint_text=self.hint_text,
            hint_style=self.hint_style,
            text_style=self.text_style,
            expand=self.expand,
            border_radius=self.border_radius,
            border_color=self.border_color,
            bgcolor=self.bgcolor,
            cursor_color=self.cursor_color,
            content_padding=self.content_padding,
            password=self.password,
            can_reveal_password=self.can_reveal_password,
            on_submit=self.on_submit,
        )


class Table(DataTable):
    def __init__(self, vis: bool) -> None:
        super().__init__()
        self.border = border.all(2, colors.SURFACE_VARIANT)
        self.border_radius = 8
        self.divider_thickness = 0
        self.heading_row_height = 75
        self.horizontal_lines = border.BorderSide(1, colors.PRIMARY)
        self.heading_text_style = TextStyle(
            color=colors.ON_SURFACE_VARIANT, weight=FontWeight.BOLD
        )
        self.data_text_style = TextStyle(
            color=colors.ON_SURFACE_VARIANT, weight=FontWeight.W_600
        )
        self.data_row_color = {MaterialState.HOVERED: colors.SURFACE_VARIANT}
        self.width = 10000
        self.visible = vis

    def build(self) -> DataTable:
        return DataTable(
            border=self.border,
            border_radius=self.border_radius,
            divider_thickness=self.divider_thickness,
            heading_row_height=self.heading_row_height,
            horizontal_lines=self.horizontal_lines,
            heading_text_style=self.heading_text_style,
            data_text_style=self.data_text_style,
            data_row_color=self.data_row_color,
            width=self.width,
            visible=self.visible,
        )


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

    def build(self) -> IconButton:
        return IconButton(icon=self.icon, style=self.style, on_click=self.on_click)
