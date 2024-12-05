import flet as ft


def main(page: ft.Page):
    page.spacing = 0
    page.padding = 0

    def handle_expansion_tile_change(e):
        page.open(
            ft.SnackBar(
                ft.Text(f"ExpansionTile was {'expanded' if e.data == 'true' else 'collapsed'}"),
                duration=1000,
            )
        )
        if e.control.trailing:
            e.control.trailing.name = (
                ft.icons.ARROW_DROP_DOWN
                if e.control.trailing.name == ft.icons.ARROW_DROP_DOWN_CIRCLE
                else ft.icons.ARROW_DROP_DOWN_CIRCLE
            )
            page.update()

    expansion_tiles = ft.Column(
        [
            ft.ExpansionTile(
                title=ft.Text("ExpansionTile 1"),
                subtitle=ft.Text("Trailing expansion arrow icon"),
                affinity=ft.TileAffinity.PLATFORM,
                maintain_state=True,
                collapsed_text_color=ft.colors.RED,
                text_color=ft.colors.RED,
                controls=[ft.ListTile(title=ft.Text("This is sub-tile number 1"))],
            ),
            ft.ExpansionTile(
                title=ft.Text("ExpansionTile 2"),
                subtitle=ft.Text("Custom expansion arrow icon"),
                trailing=ft.Icon(ft.icons.ARROW_DROP_DOWN),
                collapsed_text_color=ft.colors.GREEN,
                text_color=ft.colors.GREEN,
                on_change=handle_expansion_tile_change,
                controls=[ft.ListTile(title=ft.Text("This is sub-tile number 2"))],
            ),
            ft.ExpansionTile(
                title=ft.Text("ExpansionTile 3"),
                subtitle=ft.Text("Leading expansion arrow icon"),
                affinity=ft.TileAffinity.LEADING,
                initially_expanded=True,
                collapsed_text_color=ft.colors.BLUE,
                text_color=ft.colors.BLUE,
                controls=[
                    ft.ListTile(title=ft.Text("This is sub-tile number 3")),
                    ft.ListTile(title=ft.Text("This is sub-tile number 4")),
                    ft.ListTile(title=ft.Text("This is sub-tile number 5")),
                ],
            ),
        ],
        expand=True,
    )

    page.add(
        ft.Row(
            [
                ft.Container(expansion_tiles, expand=False, width=300),
                ft.VerticalDivider(width=1),
                ft.Container(
                    content=ft.Text("Main Content Area"),
                    expand=True,
                    alignment=ft.alignment.center,
                ),
            ],
            expand=True,
        )
    )


ft.app(main)
