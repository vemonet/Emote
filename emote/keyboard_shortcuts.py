import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from emote import config, user_data
from emote.keybinding import ButtonKeybinding


GRID_SIZE = 10


class KeyboardShortcuts(Gtk.Dialog):
    def __init__(self, update_accelerator):
        Gtk.Dialog.__init__(
            self,
            # window_position=Gtk.WindowPosition.CENTER,
            resizable=False,
        )

        self.update_accelerator = update_accelerator

        header = Gtk.HeaderBar(title_widget=Gtk.Label(label="Keyboard Shortcuts"))
        self.set_titlebar(header)

        box = self.get_content_area()

        shortcuts_grid = Gtk.Grid(
            orientation=Gtk.Orientation.VERTICAL,
            # margin=GRID_SIZE,
            row_spacing=GRID_SIZE,
        )
        shortcuts_grid.set_row_homogeneous(False)
        shortcuts_grid.set_column_homogeneous(True)

        row = 1

        if not config.is_wayland:
            open_label = Gtk.Label(label="Open Emoji Picker")
            open_label.set_xalign(0)
            open_label.set_yalign(0.5)
            shortcuts_grid.attach(open_label, 1, row, 1, 1)
            open_keybinding = ButtonKeybinding()
            open_keybinding.set_size_request(150, -1)
            open_keybinding.connect("accel-edited", self.on_kb_changed)
            open_keybinding.connect("accel-cleared", self.on_kb_changed)
            accel_string, _ = user_data.load_accelerator()
            open_keybinding.set_accel_string(accel_string)
            shortcuts_grid.attach(open_keybinding, 2, row, 1, 1)
            row += 1

        select_label = Gtk.Label(label="Select Emoji")
        select_label.set_xalign(0)
        select_label.set_yalign(0.5)
        shortcuts_grid.attach(select_label, 1, row, 1, 1)
        select_shortcut = Gtk.ShortcutsShortcut(accelerator="Return")
        shortcuts_grid.attach(select_shortcut, 2, row, 1, 1)
        row += 1

        select_multi_label = Gtk.Label(label="Add Emoji to Selection")
        select_multi_label.set_xalign(0)
        select_multi_label.set_yalign(0.5)
        shortcuts_grid.attach(select_multi_label, 1, row, 1, 1)
        select_multi_shortcut = Gtk.ShortcutsShortcut(accelerator="<Shift>+Return")
        shortcuts_grid.attach(select_multi_shortcut, 2, row, 1, 1)
        row += 1

        search_label = Gtk.Label(label="Focus Search")
        search_label.set_xalign(0)
        search_label.set_yalign(0.5)
        shortcuts_grid.attach(search_label, 1, row, 1, 1)
        search_shortcut = Gtk.ShortcutsShortcut(accelerator="<Ctrl>+F")
        shortcuts_grid.attach(search_shortcut, 2, row, 1, 1)
        row += 1

        next_cat_label = Gtk.Label(label="Next Emoji Category")
        next_cat_label.set_xalign(0)
        next_cat_label.set_yalign(0.5)
        shortcuts_grid.attach(next_cat_label, 1, row, 1, 1)
        next_cat_shortcut = Gtk.ShortcutsShortcut(accelerator="<Ctrl>+Tab")
        shortcuts_grid.attach(next_cat_shortcut, 2, row, 1, 1)
        row += 1

        prev_cat_label = Gtk.Label(label="Previous Emoji Category")
        prev_cat_label.set_xalign(0)
        prev_cat_label.set_yalign(0.5)
        shortcuts_grid.attach(prev_cat_label, 1, row, 1, 1)
        prev_cat_label = Gtk.ShortcutsShortcut(accelerator="<Ctrl>+<Shift>+Tab")
        shortcuts_grid.attach(prev_cat_label, 2, row, 1, 1)
        row += 1

        box.append(shortcuts_grid)

        self.present()

    def on_kb_changed(self, button_keybinding, accel_string=None, accel_label=None):
        self.update_accelerator(accel_string, accel_label)
