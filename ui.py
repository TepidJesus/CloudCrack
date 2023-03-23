from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tabs, Tab, Label

class HomeApp(App):

    # Add a binding to switch tabs when it is clicked
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("tab", "tabs:activate_next", "Switch tabs")]

    def compose(self) -> ComposeResult:
        yield Tabs(
        Tab("First tab", id="one"),
        Tab("Second tab", id="two"),
    )
        yield Header()
        yield Label("Select a tab")
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Handle TabActivated message sent by Tabs."""
        label = self.query_one(Label)
        if event.tab is None:
            # When the tabs are cleared, event.tab will be None
            label.visible = False
        else:
            label.visible = True
            label.update(event.tab.label)    


def main():
    app = HomeApp()
    app.run()

main()