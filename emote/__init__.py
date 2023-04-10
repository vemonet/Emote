import sys
import gi
import manimpango
from setproctitle import setproctitle

gi.require_version("Gtk", "4.0")
gi.require_version("Keybinder", "3.0")
from gi.repository import Gtk, Keybinder

from emote import picker, css, emojis, user_data, config

# Register updated emoji font
if config.is_snap:
    manimpango.register_font(f"{config.snap_root}/static/NotoColorEmoji.ttf")
elif config.is_flatpak:
    manimpango.register_font(f"{config.flatpak_root}/static/NotoColorEmoji.ttf")
else:
    manimpango.register_font("static/NotoColorEmoji.ttf")

settings = Gtk.Settings.get_default()


class EmoteApplication(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="com.tomjwatson.Emote", **kwargs)

        self.activated = False
        self.picker_window = None

    def start_daemon(self):
        setproctitle("emote")

        if not config.is_wayland:
            # Keybinder.init()
            self.set_accelerator()

        print("Before load CSS")
        css.load_css()
        print("Before emo")
        emojis.init()
        print("After load CSS")

        self.activated = True

        # The first time the app launches, open the picker and show the
        # guide
        self.create_picker_window(True)
        if not user_data.load_shown_welcome():
            user_data.update_shown_welcome()

        self.set_theme()
        print("After set theme")

        # https://docs.gtk.org/gtk4/migrating-3to4.html#stop-using-gtk_main-and-related-apis
        # Run the main gtk event loop - this prevents the app from quitting
        # Gtk.main()

    def set_accelerator(self):
        """Register global shortcut for invoking the emoji picker"""
        accel_string, _ = user_data.load_accelerator()

        # if accel_string:
        #     Keybinder.bind(accel_string, self.handle_accelerator)

    def set_theme(self):
        """Set the GTK theme to be used for the app windows"""
        theme = user_data.load_theme()

        if theme != user_data.DEFAULT_THEME:
            print(f"Setting theme to {theme}")
            settings.set_property("gtk-theme-name", theme)
        else:
            settings.reset_property("gtk-theme-name")

    def unset_accelerator(self):
        old_accel_string, _ = user_data.load_accelerator()

        # if old_accel_string:
        #     Keybinder.unbind(old_accel_string)

    def handle_accelerator(self, keystring):
        if self.picker_window:
            self.picker_window.destroy()
        else:
            self.create_picker_window()

    def update_accelerator(self, accel_string, accel_label):
        print(f"Updating global shortcut to {accel_label}")
        self.unset_accelerator()
        user_data.update_accelerator(accel_string, accel_label)
        self.set_accelerator()

    def update_theme(self, theme):
        user_data.update_theme(theme)
        self.set_theme()

    def create_picker_window(self, show_welcome=False):
        if self.picker_window:
            self.picker_window.destroy()
        self.picker_window = picker.EmojiPicker(
            Keybinder.get_current_event_time() if Keybinder else 1,
            self.update_accelerator,
            self.update_theme,
            show_welcome,
        )
        self.picker_window.connect("destroy", self.handle_picker_destroy)

    def handle_picker_destroy(self, *args):
        self.picker_window = None

    def do_activate(self):
        if not self.activated:
            print("Launching emote daemon")
            self.start_daemon()
        else:
            print("Second instance launched")
            self.create_picker_window()


def main():
    app = EmoteApplication()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
