import os.path
import sys

from gi.repository import Gio

from rencher import tmp_path
from rencher.gtk import compile_data


def main() -> None:
    compile_data()

    # ui files get loaded when the import happens
    # we want the ui that we just compiled`
    from rencher.gtk.application import RencherApplication  # noqa: E402	
    app = RencherApplication()

    gres_path = os.path.join(tmp_path, 'rencher/gtk/res/resources.gresource')
    res = Gio.resource_load(gres_path)
    res._register()  # type: ignore

    try:
        app.run(sys.argv)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()