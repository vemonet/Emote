import os
import time
from datetime import datetime
import gi
from itertools import zip_longest

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib, Gio, Pango
from gi.repository.GdkPixbuf import Pixbuf
from emote import (
    emojis,
    user_data,
    settings,
    keyboard_shortcuts,
    guide,
    config,
    debouncer,
)

GRID_SIZE = 10
EMOJIS_PER_ROW = 10


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

# GTK3 to GTK4 migration: https://docs.gtk.org/gtk4/migrating-3to4.html#adapt-to-gtkwindow-api-changes
# GTK4 example: https://github.com/mijorus/smile/blob/master/src/Picker.py
class EmojiPicker(Gtk.ApplicationWindow):
    def __init__(self, open_time, update_accelerator, update_theme, show_welcome):
        Gtk.Window.__init__(
            self,
            title="Emote",
            # window_position=Gtk.WindowPosition.CENTER,
            resizable=False,
            deletable=False,
            name="emote_window",
        )
        self.set_default_size(500, 450)
        # self.set_keep_above(True)
        self.dialog_open = False
        self.update_accelerator = update_accelerator
        self.update_theme = update_theme
        self.search_scrolled = None
        self.emoji_append_list = []
        self.current_emojis = []
        self.first_emoji_widget = None
        self.target_emoji = None
        self.search_debouncer = debouncer.SearchDebouncer(self.search_callback)

        # https://docs.gtk.org/gtk4/migrating-3to4.html#reduce-the-use-of-generic-container-apis
        self.app_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.app_container)

        self.init_header()
        self.init_category_selectors()
        self.init_action_bar()
        self.render_selected_emoji_category()

        self.present_with_time(open_time)

        self.check_welcome(show_welcome)

        # Delay registering events by 100ms. For some reason FOCUS of Window is
        # momentarily False during window creation.
        GLib.timeout_add(500, self.register_window_state_event_handler)

        # self.connect("key-pressed", self.on_key_press_event)
        window_key_controller = Gtk.EventControllerKey()
        print("CONTRO")
        window_key_controller.connect(
            'key-pressed',
            self.on_key_press_event
            # lambda q, w, e, r: self.default_hiding_action() if w == Gdk.KEY_Escape else False
        )
        self.add_controller(window_key_controller)

    def init_header(self):
        header = Gtk.HeaderBar(name="header", hexpand=True)
        widget = Gtk.Box(hexpand=True)

        self.search_entry = Gtk.SearchEntry(hexpand=True)
        # https://docs.gtk.org/gtk4/migrating-3to4.html#stop-using-gtkwidget-event-signals
        # self.search_entry.connect("focused-in", self.on_search_focused)
        self.search_entry.connect("search-changed", self.on_search_changed)
        # self.search_entry.connect('activate', self.handle_search_entry_activate)
        # self.search_entry.connect("key-pressed", self.on_search_entry_key_press_event)
        search_key_controller = Gtk.EventControllerKey()
        search_key_controller.connect(
            'key-pressed',
            self.on_key_press_event
            # self.on_search_entry_key_press_event
        )
        self.search_entry.add_controller(search_key_controller)

        widget.append(self.search_entry)
        header.set_title_widget(widget)
        # header.pack_start(widget)

        GLib.idle_add(self.search_entry.grab_focus)

        header.pack_end(self.init_menu_button())
        header.pack_end(self.init_skintone_button())

        self.set_titlebar(header)

    def init_menu_button(self):
        self.menu_popover = Gtk.Popover()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        items_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        if config.is_snap or config.is_dev:
            prefs_btn = Gtk.Button(label="Preferences")
            prefs_btn.set_halign(0)
            prefs_btn.set_valign(0.5)
            prefs_btn.connect("clicked", lambda prefs_btn: self.open_preferences())
            items_box.append(prefs_btn, False, True, 0)

        keyboard_shortcuts_btn = Gtk.Button(label="Keyboard Shortcuts")
        keyboard_shortcuts_btn.set_halign(0)
        keyboard_shortcuts_btn.set_valign(0.5)
        keyboard_shortcuts_btn.connect(
            "clicked", lambda keyboard_shortcuts_btn: self.open_keyboard_shortcuts()
        )
        items_box.append(keyboard_shortcuts_btn)

        guide_btn = Gtk.Button(label="Guide")
        guide_btn.set_halign(0)
        guide_btn.set_valign(0.5)
        guide_btn.connect("clicked", lambda guide_btn: self.open_guide())
        items_box.append(guide_btn)

        about_btn = Gtk.Button(label="About")
        about_btn.set_halign(0)
        about_btn.set_valign(0.5)
        about_btn.connect("clicked", lambda about_btn: self.open_about())
        items_box.append(about_btn)

        vbox.append(items_box)
        hbox.append(vbox)
        self.menu_popover.set_child(hbox)
        self.menu_popover.set_position(Gtk.PositionType.BOTTOM)

        menu_button = Gtk.MenuButton(name="menu_button")
        menu_button.set_popover(self.menu_popover)
        menu_button.show()
        menu_button.set_child(
            Gtk.Image.new_from_gicon(
                Gio.ThemedIcon(name="open-menu-symbolic")
            )
        )

        return menu_button

    def init_skintone_button(self):
        skintone_combo = Gtk.ComboBoxText()
        skintone_combo.set_entry_text_column(0)
        skintone_combo.connect("changed", self.on_skintone_combo_changed)

        for skintone in user_data.SKINTONES:
            skintone_combo.append_text(skintone)

        skintone_combo.set_active(user_data.load_skintone_index())

        return skintone_combo

    def on_skintone_combo_changed(self, combo):
        char = combo.get_active_text()

        skintone_index = None

        if char == "✋":
            skintone_index = 0
        elif char == "✋🏻":
            skintone_index = 1
        elif char == "✋🏼":
            skintone_index = 2
        elif char == "✋🏽":
            skintone_index = 3
        elif char == "✋🏾":
            skintone_index = 4
        elif char == "✋🏿":
            skintone_index = 5

        if skintone_index is not None:
            user_data.update_skintone_index(skintone_index)

            query = self.search_entry.props.text
            if query == "":
                if hasattr(self, "selected_emoji_category"):
                    self.render_selected_emoji_category()
            else:
                self.render_emoji_search_results(query)

    def init_category_selectors(self):
        self.categories_box = Gtk.Box(
            halign=Gtk.Align.CENTER,
            spacing=10,
            margin_start=10,
            margin_end=10,
            margin_bottom=GRID_SIZE,
            margin_top=GRID_SIZE
        )

        self.category_selectors = []
        self.selected_emoji_category = "recent"

        for category, _, category_image in emojis.get_category_order():
            category_selector = Gtk.ToggleButton(
                label=category_image, name="category_selector_button"
            )
            category_selector.set_tooltip_text(self.get_category_display_name(category))
            category_selector.category = category

            if category == self.selected_emoji_category:
                category_selector.set_active(True)

            self.category_selectors.append(category_selector)

            category_selector.connect("toggled", self.on_category_selector_toggled)

            self.categories_box.append(category_selector)

        self.app_container.append(self.categories_box)

    def init_action_bar(self):
        self.action_bar = Gtk.ActionBar()

        self.emoji_preview_box = Gtk.Box(
            spacing=GRID_SIZE, orientation=Gtk.Orientation.HORIZONTAL
            # margin=GRID_SIZE,
        )

        self.previewed_emoji_label = Gtk.Label(label=" ")
        self.previewed_emoji_label.set_name("previewed_emoji_label")
        self.previewed_emoji_label.set_xalign(0)
        self.previewed_emoji_label.set_yalign(0.2)
        self.emoji_preview_box.append(self.previewed_emoji_label)

        self.emoji_preview_box_text = Gtk.Box(
            spacing=0, orientation=Gtk.Orientation.VERTICAL
        )
        self.previewed_emoji_name_label = Gtk.Label(
            label=" ", ellipsize=Pango.EllipsizeMode.END
        )
        self.previewed_emoji_name_label.set_name("previewed_emoji_name_label")
        self.previewed_emoji_name_label.set_xalign(0)
        self.previewed_emoji_name_label.set_yalign(0.2)
        self.emoji_preview_box_text.append(self.previewed_emoji_name_label)

        self.previewed_emoji_shortcode_label = Gtk.Label(
            label=" ", ellipsize=Pango.EllipsizeMode.END
        )
        self.previewed_emoji_shortcode_label.set_name("previewed_emoji_shortcode_label")
        self.previewed_emoji_shortcode_label.set_xalign(0)
        self.previewed_emoji_shortcode_label.set_yalign(0.2)
        self.emoji_preview_box_text.append(self.previewed_emoji_shortcode_label)

        self.emoji_preview_box.append(self.emoji_preview_box_text)

        self.action_bar.pack_start(self.emoji_preview_box)

        self.selected_box = Gtk.Box(
            spacing=GRID_SIZE, margin_bottom=0
        )

        self.emoji_append_list_preview = Gtk.Label(
            label=" ", max_width_chars=25, ellipsize=Pango.EllipsizeMode.START
        )
        self.emoji_append_list_preview.set_name("emoji_append_list_preview")
        self.selected_box.append(self.emoji_append_list_preview)

        self.action_bar.pack_end(self.selected_box)
        self.selected_box.hide()

        self.app_container.append(self.action_bar)

    def get_skintone_char(self, emoji):
        char = emoji["char"]

        if emoji["skintone"] is None:
            return char

        skintone = user_data.load_skintone_index()

        if skintone == 0:
            return char

        try:
            return emoji["skintone"][str(skintone)]["char"]
        except Exception:
            return char

    def show_emoji_preview(self, char):
        emoji = emojis.get_emoji_by_char(char)

        self.previewed_emoji_label.set_text(self.get_skintone_char(emoji))
        self.previewed_emoji_shortcode_label.set_text(f':{emoji["shortcode"]}:')
        self.previewed_emoji_name_label.set_text(emoji["name"])

    def reset_emoji_preview(self):
        if len(self.current_emojis) > 0:
            self.show_emoji_preview(self.target_emoji)
        else:
            self.previewed_emoji_label.set_text(" ")
            self.previewed_emoji_name_label.set_text(" ")
            self.previewed_emoji_shortcode_label.set_text(" ")

    def update_emoji_append_list_preview(self):
        self.emoji_append_list_preview.set_text("".join(self.emoji_append_list))

    def check_welcome(self, show_welcome):
        """Show the guide the first time we run the app"""
        if show_welcome:
            self.open_guide()

    def register_window_state_event_handler(self):
        # self.connect("window-state-event", self.on_window_state_event)
        print("TODO: ")

    def on_window_state_event(self, widget, event):
        """If the window has just unfocused, exit"""
        if self.dialog_open:
            return

        if config.is_debug:
            return

        if not (event.new_window_state & Gdk.WindowState.FOCUSED):
            self.destroy()

    # def handle_window_key_press(self, controller: Gtk.EventController, keyval: int, keycode: int, state: Gdk.ModifierType) -> bool:
    def on_key_press_event(self, controller: Gtk.EventController, keyval: int, keycode: int, state: Gdk.ModifierType):
        print(keyval, Gdk.KEY_Escape)
        print(keycode)
        print(controller, state)
        if keyval == Gdk.KEY_Escape:
            print("DESTROYING")
            self.destroy()
            return True
        else:
            return False
        # keyval = event.keyval
        # keyval_name = Gdk.keyval_name(keyval)
        # state = event.state
        # ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        # shift = bool(state & Gdk.ModifierType.SHIFT_MASK)
        # tab = keyval_name == "Tab" or keyval_name == "ISO_Left_Tab"

        # if ctrl and keyval_name == "f":
        #     self.search_entry.grab_focus()
        # elif ctrl and shift and tab:
        #     self.on_cycle_category(True)
        # elif ctrl and tab:
        #     self.on_cycle_category()
        # elif keyval_name == "Escape":
        #     self.destroy()
        # else:
        #     return False
        return True

    def open_preferences(self):
        self.dialog_open = True
        settings_window = settings.Settings(self.update_theme)
        settings_window.connect("destroy", self.on_close_dialog)

    def open_keyboard_shortcuts(self):
        self.dialog_open = True
        keyboard_shortcuts_window = keyboard_shortcuts.KeyboardShortcuts(
            self.update_accelerator
        )
        keyboard_shortcuts_window.connect("destroy", self.on_close_dialog)

    def open_guide(self):
        self.dialog_open = True
        guide_window = guide.Guide()
        guide_window.connect("destroy", self.on_close_dialog)

    def open_about(self):
        about_dialog = Gtk.AboutDialog(
            transient_for=self,
            modal=True,
            logo_icon_name='com.tomjwatson.Emote',
            program_name="Emote",
            title="About Emote",
            version=os.environ.get("FLATPAK_APP_VERSION", "dev build"),
            authors=["Tom Watson", "Vincent Emonet"],
            artists=["Tom Watson, Matthew Wong"],
            documenters=["Irene Auñón"],
            copyright=f"© Tom Watson {datetime.now().year}",
            website_label="Source Code",
            website="https://github.com/tom-james-watson/emote",
            comments="Modern popup emoji picker",
            license_type=Gtk.License.GPL_3_0,
        )

        self.dialog_open = True
        about_dialog.present()
        about_dialog.connect("destroy", self.on_close_dialog)

    def on_close_dialog(self, dialog):
        self.dialog_open = False

    def on_search_entry_key_press_event(self, widget, event):
        keyval = event.keyval
        keyval_name = Gdk.keyval_name(keyval)
        shift = bool(event.state & Gdk.ModifierType.SHIFT_MASK)

        print("SEARCHY", keyval, keyval_name)
        if shift and keyval_name == "Return":
            if len(self.current_emojis) > 0:
                self.on_emoji_append(self.get_skintone_char(self.current_emojis[0]))
        elif keyval_name == "Return":
            if len(self.current_emojis) > 0:
                self.on_emoji_select(self.get_skintone_char(self.current_emojis[0]))
        elif keyval_name == "Down" and self.first_emoji_widget:
            self.first_emoji_widget.grab_focus()
        else:
            return False

        return True

    def on_category_selector_toggled(self, toggled_category_selector):
        if not toggled_category_selector.get_active():
            return

        self.selected_emoji_category = toggled_category_selector.category

        for category_selector in self.category_selectors:
            if category_selector.category != self.selected_emoji_category:
                category_selector.set_active(False)

        self.search_entry.set_text("")
        self.render_selected_emoji_category()

    def on_cycle_category(self, backwards=False):
        index = None

        for i, category_selector in enumerate(self.category_selectors):
            if category_selector.category == self.selected_emoji_category:
                index = i
                break

        if backwards:
            if index == 0:
                index = -1
            else:
                index -= 1
        else:
            if index == len(self.category_selectors) - 1:
                index = 0
            else:
                index += 1

        toggled_category_selector = self.category_selectors[index]
        toggled_category_selector.set_active(True)
        toggled_category_selector.grab_focus()

        self.on_category_selector_toggled(toggled_category_selector)

    def on_search_focused(self, search_entry, event):
        if len(self.current_emojis) > 0:
            self.target_emoji = self.get_skintone_char(self.current_emojis[0])
        self.reset_emoji_preview()

    def on_search_changed(self, search_entry):
        self.search_debouncer.search(self.search_entry.props.text)

    def search_callback(self, query):
        if query == "":
            if hasattr(self, "search_scrolled") and self.search_scrolled:
                self.app_container.remove(self.search_scrolled)

            self.categories_box.show()

            self.render_selected_emoji_category()

        else:
            self.app_container.remove(self.category_scrolled)
            self.render_emoji_search_results(query)

    def render_emoji_search_results(self, query):
        if hasattr(self, "search_scrolled") and self.search_scrolled:
            self.app_container.remove(self.search_scrolled)

        self.search_scrolled = Gtk.ScrolledWindow(
            propagate_natural_height=True,
            propagate_natural_width=True,
            vexpand=True,
            hexpand=False,
        )

        search_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            # spacing=GRID_SIZE,
            margin_top=GRID_SIZE,
        )
        search_box.append(self.create_emoji_results(emojis.search(query)))

        self.search_scrolled.set_child(search_box)
        self.app_container.append(self.search_scrolled)
        self.app_container.reorder_child_after(self.search_scrolled, None)

        self.categories_box.hide()

    def get_category_display_name(self, category):
        category_display_name = None

        for c, display_name, _ in emojis.get_category_order():
            if c == category:
                category_display_name = display_name
                break

        return category_display_name

    def render_selected_emoji_category(self):
        if hasattr(self, "category_scrolled"):
            self.app_container.remove(self.category_scrolled)

        self.category_scrolled = Gtk.ScrolledWindow(
            propagate_natural_height=True,
            propagate_natural_width=True,
            vexpand=True,
            hexpand=False,
            # min_content_height=350,
        )

        category = self.selected_emoji_category

        category_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        label_box = Gtk.Box()
        # label = Gtk.Label(margin_right=GRID_SIZE, margin_left=GRID_SIZE)
        label = Gtk.Label(name="category_label")
        label.set_text(self.get_category_display_name(category))
        label.set_justify(Gtk.Justification.LEFT)
        label_box.append(label)
        category_box.append(Gtk.Box())
        category_box.append(label_box)

        category_box.append(self.create_emoji_results(emojis.get_emojis_by_category()[category], True))

        self.category_scrolled.set_child(category_box)
        self.app_container.append(self.category_scrolled)
        self.app_container.reorder_child_after(self.category_scrolled, self.categories_box)


    # Main list of emojis is generated here
    def create_emoji_results(self, emojis, for_category=False):
        self.current_emojis = emojis

        if len(emojis) > 0:
            self.target_emoji = self.get_skintone_char(emojis[0])
        self.reset_emoji_preview()

        results_grid = Gtk.Grid(
            orientation=Gtk.Orientation.VERTICAL,
            # margin=GRID_SIZE,
            margin_bottom=0,
            margin_top=GRID_SIZE if for_category else 0,
        )
        results_grid.set_row_homogeneous(True)
        results_grid.set_column_homogeneous(True)

        row = 0

        for emoji_row in grouper(emojis, EMOJIS_PER_ROW, None):
            row += 1
            column = 0

            for emoji in emoji_row:
                column += 1

                if emoji is None:
                    btn = Gtk.Button(
                        label=" ",
                        name="emoji_button",
                        can_focus=False,
                        # relief=Gtk.ReliefStyle.NONE,
                        has_frame=False,
                        sensitive=False,
                    )
                else:
                    gesture_left = Gtk.GestureClick(button=Gdk.BUTTON_PRIMARY, name=self.get_skintone_char(emoji))
                    gesture_right = Gtk.GestureClick(button=Gdk.BUTTON_SECONDARY, name=self.get_skintone_char(emoji))
                    hover = Gtk.EventControllerMotion(name=self.get_skintone_char(emoji))
                    btn = Gtk.Button(
                        label=self.get_skintone_char(emoji),
                        name="emoji_button",
                        can_focus=True,
                        has_frame=False,
                    )
                    gesture_left.connect("pressed", self.on_emoji_btn_left_click)
                    gesture_right.connect("pressed", self.on_emoji_btn_right_click)
                    hover.connect("enter", self.on_emoji_hover)
                    hover.connect("leave", self.on_emoji_leave)
                    btn.add_controller(gesture_left)
                    btn.add_controller(gesture_right)
                    btn.add_controller(hover)

                if row == 1 and column == 1:
                    self.first_emoji_widget = btn

                btn.set_size_request(10, 10)

                btn_af = Gtk.AspectFrame(
                    xalign=0.5, yalign=0.5, ratio=1.0, name="emoji_button_af"
                )
                btn_af.set_child(btn)

                results_grid.attach(btn_af, column, row, 1, 1)

        return results_grid

    def on_emoji_btn_left_click(self, btn, some_int, x, y):
        self.on_emoji_select(btn.get_name())

        # TODO: handle focus change and click with shift (append to emoji list)
        # elif event.type == Gdk.EventType.FOCUS_CHANGE:
        #     self.target_emoji = emoji
        #     self.show_emoji_preview(emoji)

    def on_emoji_btn_right_click(self, btn, some_int, x, y):
        # Right mouse clicked
        self.on_emoji_append(btn.get_name())

    def on_emoji_hover(self, btn, some_int, x):
        self.show_emoji_preview(btn.get_name())

    def on_emoji_leave(self, btn):
        self.reset_emoji_preview()

    def on_emoji_append(self, emoji):
        """Append the selected emoji to the clipboard"""
        print(f"Appending {emoji} to selection")
        self.emoji_append_list.append(emoji)

        if len(self.emoji_append_list) == 1:
            self.previewed_emoji_name_label.set_max_width_chars(20)
            self.previewed_emoji_shortcode_label.set_max_width_chars(20)

        self.update_emoji_append_list_preview()

        self.copy_to_clipboard("".join(self.emoji_append_list))
        self.add_emoji_to_recent(emoji)

    def on_emoji_select(self, emoji):
        """
        Copy the selected emoji to the clipboard, close the picker window and
        make the user's system perform a paste after 150ms, pasting the emoji
        to the currently focused application window.

        If we have been appending other emojis first, add this final one first.
        """
        self.hide()

        if len(self.emoji_append_list) > 0:
            self.on_emoji_append(emoji)
        else:
            print(f"Selecting {emoji}")
            self.add_emoji_to_recent(emoji)
            self.copy_to_clipboard(emoji)

        self.destroy()

        if not config.is_wayland:
            time.sleep(0.15)
            os.system("xdotool key ctrl+v")

    def add_emoji_to_recent(self, emoji):
        user_data.update_recent_emojis(emoji)
        emojis.update_recent_category()

    def copy_to_clipboard(self, content):
        cb = Gdk.Display.get_default().get_clipboard()
        content_provider = Gdk.ContentProvider.new_for_value(content)
        cb.set_content(content_provider)
