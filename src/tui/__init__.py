import os

from dotenv import load_dotenv


def debug_notify(self, *args, **kwargs) -> None:
    load_dotenv()
    if os.getenv('DOSSIER_BUILD') == 'debug':
        self.notify(*args, **kwargs)
