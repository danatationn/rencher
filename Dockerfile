FROM ubuntu:25.10
LABEL authors="danatationn"

RUN apt update && apt install -y \
	python3-dev \
    python3-pip \
    python3-venv \
    cmake \
	gobject-introspection \
	libgirepository1.0-dev \
	libgirepository-2.0-dev \
	libgtk-4-dev \
	patchelf \
	libadwaita-1-dev \
	ccache \
	blueprint-compiler \
    file \
    flatpak-builder \
    flatpak \
	meson
WORKDIR /app
COPY . .
RUN pip install uv --break-system-packages
RUN uv sync
RUN . .venv/bin/activate && meson setup build -Dprefix=$(pwd)/build/root
RUN . .venv/bin/activate && ninja -C build install
RUN flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo --system
RUN flatpak install org.gnome.Sdk//49 org.gnome.Platform//49 --system -y
RUN flatpak-builder --disable-sandbox --disable-rofiles-fuse --install --user build/flatpak com.github.danatationn.rencher.yml
RUN flatpak build-bundle ~/.local/share/flatpak/repo Rencher.flatpak com.github.danatationn.rencher
