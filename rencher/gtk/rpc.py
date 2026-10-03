import asyncio
import logging
import threading
from typing import cast

from gi.repository import Gio, GLib
from pypresence.exceptions import DiscordNotFound
from pypresence.presence import AioPresence

TIMEOUT_SECS = 1

type PresenceValue = str | int | float | bool | list[str] | None

class Rpc:
    """
        rpc helper class

        handles cases where discord restarts, or when rpc is turned off and turned on again
    """
    action_group: Gio.SimpleActionGroup

    client_id: int
    _presence: AioPresence | None
    _running: bool

    _current_state: dict[str, PresenceValue] | None
    _state_changed: bool

    _thread: threading.Thread | None
    _loop: asyncio.AbstractEventLoop | None

    _discord_found: bool

    def __init__(self, client_id: int):
        self.client_id = client_id
        self._presence = None
        self._running = False

        self._current_state = None
        self._state_changed = False

        self._thread = None
        self._loop = None

        self._discord_found = True

        self.action_group = Gio.SimpleActionGroup()

        start_action = Gio.SimpleAction.new('start')
        start_action.connect('activate', self._start)
        self.action_group.add_action(start_action)

        stop_action = Gio.SimpleAction.new('stop')
        stop_action.connect('activate', self._stop)
        self.action_group.add_action(stop_action)

        # s=key, s=value
        update_action = Gio.SimpleAction.new('update', GLib.VariantType('a(ss)'))
        update_action.connect('activate', self._update)
        self.action_group.add_action(update_action)

        clear_action = Gio.SimpleAction.new('clear')
        clear_action.connect('activate', self._clear)
        self.action_group.add_action(clear_action)

    async def _connect(self) -> bool:
        try:
            self._presence = AioPresence(self.client_id)
            await self._presence.connect()
            logging.info('RPC connected')
            self._discord_found = True
            return True
        except DiscordNotFound as e:
            # without this it will spam the console
            if self._discord_found:
                logging.warning(e)
                self._discord_found = False
            return False
        except Exception as e:
            self._presence = None
            logging.error(e)
            return False

    async def _run_loop(self):
        """ loop that checks if the rpc is connected and if it is, it updates it only when the state changes """
        while self._running:
            if await self._connect():
                self._current_state = None
                self._state_changed = False
                try:
                    while self._running and self._presence:
                        await asyncio.sleep(TIMEOUT_SECS)
                        if self._state_changed:
                            if self._current_state:
                                await self._presence.update(**self._current_state)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                            elif not self._current_state:
                                await self._presence.clear()
                            logging.debug(f'RPC updated ({self._current_state})')
                            self._state_changed = False
                except Exception:
                    pass

            if self._running:
                await asyncio.sleep(TIMEOUT_SECS)

    def _start_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._run_loop())

    def _start(self, _rpc: 'Rpc', _param: GLib.Variant | None) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._start_loop, daemon=True)
        self._thread.start()

    def _update(self, _rpc: 'Rpc', param: GLib.Variant | None) -> None:
        if param:
            pairs = cast(list[tuple[str, str]], param.unpack())
            self._current_state = dict(pairs)
        else:
            self._current_state = {}
        self._state_changed = True

    def _clear(self, _rpc: 'Rpc', _param: GLib.Variant | None) -> None:
        if self._current_state is not None:
            self._current_state = None
            self._state_changed = True

    def _stop(self, _rpc: 'Rpc', _param: GLib.Variant | None) -> None:
        self._running = False
        self._current_state = None
        self._presence = None
        self._discord_found = True
        logging.info('Stopped RPC')
