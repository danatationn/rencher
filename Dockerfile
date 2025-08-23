FROM ubuntu:25.10
LABEL authors="dan"

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
    file
WORKDIR /app
COPY . .
RUN python3 -m venv .venv
RUN . .venv/bin/activate && pip3 install -r requirements.txt
RUN . .venv/bin/activate && python3 build-aux/freeze.py
RUN . .venv/bin/activate && python3 build-aux/appimage.py