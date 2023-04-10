import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from emote import user_data


GRID_SIZE = 10


class Settings(Gtk.Dialog):
    def __init__(self, update_theme):
        Gtk.Dialog.__init__(
            self,
            # window_position=Gtk.WindowPosition.CENTER,
            resizable=False,
        )

        self.update_theme = update_theme

        header = Gtk.HeaderBar(title_widget=Gtk.Label(label="Preferences"))
        self.set_titlebar(header)

        box = self.get_content_area()

        settings_grid = Gtk.Grid(
            orientation=Gtk.Orientation.VERTICAL,
            # margin=GRID_SIZE,
            row_spacing=GRID_SIZE,
        )
        settings_grid.set_row_homogeneous(False)
        settings_grid.set_column_homogeneous(True)

        row = 1

        theme_label = Gtk.Label(title_widget=Gtk.Label(label="Theme"))
        theme_label.set_xalign(0)
        theme_label.set_yalign(0.5)
        settings_grid.attach(theme_label, 1, row, 1, 1)

        theme_combo = Gtk.ComboBoxText()
        theme_combo.set_entry_text_column(0)
        theme_combo.connect("changed", self.on_theme_combo_changed)
        for theme in user_data.THEMES:
            theme_combo.append_text(theme)
        theme_combo.set_active(user_data.THEMES.index(user_data.load_theme()))
        settings_grid.attach(theme_combo, 2, row, 1, 1)
        row += 1

        box.append(settings_grid)

        self.present()

    def on_theme_combo_changed(self, combo):
        theme = combo.get_active_text()

        if theme is not None:
            self.update_theme(theme)
