import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from emote import user_data, config


GRID_SIZE = 10


class Guide(Gtk.Dialog):
    def __init__(self):
        Gtk.Dialog.__init__(
            self,
            # title_widget=Gtk.Label(label="Emote Guide"),
            # window_position=Gtk.WindowPosition.CENTER,
            resizable=False,
        )

        header = Gtk.HeaderBar(title_widget=Gtk.Label(label="Emote Guide"))
        self.set_titlebar(header)

        box = self.get_content_area()

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        launching = Gtk.Label()
        launching.set_markup(
            '<span size="large" font_weight="bold" underline="single">Launching</span>'
        )
        # launching.set_alignment(0, 0.5)
        launching.set_xalign(0)
        launching.set_yalign(0.5)
        vbox.append(launching)

        background = Gtk.Label()
        background.set_markup(
            "Emote runs in the background and automatically starts when you log in."
        )
        background.set_wrap(True)
        # background.set_alignment(0, 0.5)
        background.set_xalign(0)
        background.set_yalign(0.5)
        vbox.append(background)

        if config.is_wayland:
            opening = Gtk.Label()
            opening.set_markup(
                "The emoji picker can be opened by clicking the app icon again, or by\n"
                'setting a custom app shortcut. See <a href="https://github.com/tom-james-watson/Emote/wiki/Hotkey-In-Wayland" title="See Wayland shortcut instructions">the wiki</a> for details.'
            )
            opening.set_wrap(True)
            opening.set_xalign(0)
            opening.set_yalign(0.5)
            vbox.append(opening)
        else:
            opening = Gtk.Label()
            opening.set_markup(
                "The emoji picker can be opened with either the keyboard shortcut or by\n"
                "clicking the app icon again."
            )
            opening.set_wrap(True)
            opening.set_xalign(0)
            opening.set_yalign(0.5)
            vbox.append(opening)

        usage = Gtk.Label()
        usage.set_markup(
            '<span size="large" font_weight="bold" underline="single">Usage</span>'
        )
        usage.set_xalign(0)
        usage.set_yalign(0.5)
        vbox.append(usage)

        if config.is_wayland:
            copying = Gtk.Label()
            copying.set_markup(
                "Select an emoji to have it copied to your clipboard. You can then paste the\n"
                "emoji wherever you need."
            )
            copying.set_wrap(True)
            copying.set_xalign(0)
            copying.set_yalign(0.5)
            vbox.append(copying)
        else:
            copying = Gtk.Label()
            copying.set_markup(
                "Select an emoji to have it pasted to your currently focused app. The\n"
                "emoji is also copied to the clipboard so you can then paste the emoji\n"
                "wherever you need."
            )
            copying.set_wrap(True)
            copying.set_xalign(0)
            copying.set_yalign(0.5)
            vbox.append(copying)

        multiple = Gtk.Label()
        multiple.set_markup(
            "You can select multiple emojis by selecting them with shift left click\n"
            "or with right click."
        )
        multiple.set_wrap(True)
        multiple.set_xalign(0)
        multiple.set_yalign(0.5)
        vbox.append(multiple)

        hbox.append(vbox)
        box.append(hbox)

        self.present()
