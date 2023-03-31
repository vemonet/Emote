OS := $(shell uname)

dev:
	ENV=dev GDK_BACKEND="x11" pipenv run start

dev-debug:
	GTK_DEBUG=interactive GDK_BACKEND="x11" ENV=dev pipenv run start

format:
	pipenv run black emote

install:
	pipenv install -d

package:
	snapcraft

clean:
	snapcraft clean

flatpak:
	flatpak-builder --user --install --force-clean build com.tomjwatson.Emote.yml
	flatpak run com.tomjwatson.Emote

flatpak-install:
	flatpak install flathub -y org.flatpak.Builder org.gnome.Platform//43 org.gnome.Sdk//43
	wget -N https://raw.githubusercontent.com/flatpak/flatpak-builder-tools/master/pip/flatpak-pip-generator
	chmod +x flatpak-pip-generator

flatpak-requirements:
	pipenv requirements > requirements.txt
	pipenv run flatpak-pip-generator --runtime='org.gnome.Sdk//43' --output python3-requirements -r requirements.txt
