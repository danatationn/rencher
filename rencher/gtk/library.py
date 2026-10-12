import logging
import os.path
import subprocess
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import IO

from gi.repository import Gio, GLib, GObject

from rencher.gtk.game_item import GameItem
from rencher.gtk.tasks import DeleteGameTask, ImportGameTask, RencherTask
from rencher.renpy.config import RencherConfig
from rencher.renpy.game import Game, GameInvalidError, GameNoExecutableError

CHECK_PROCESS_MS: int = 250


class Library(GObject.Object):
    """
    class for managing games

    stores a list of all currently loaded games, has methods for retreving and adding games

    also has actions for installing, deleting, running, closing games.

    ---

    everything akin to games happens here. any non-instant action that should be done upon a game, Should be made here
    """

    # this is all horrendous and will be refactored after v1.3.0

    action_group: Gio.SimpleActionGroup
    store: Gio.ListStore
    tasks: dict[str, RencherTask]  # str is uuid. tasks with errors stay
    processes: dict[GameItem, tuple[subprocess.Popen[bytes], float]]  # float is time
    _terminating_processes: list[subprocess.Popen[bytes]]

    _pool_generation: uuid.UUID | None
    _thread_pool: ThreadPoolExecutor

    # signal name: flags, return types, arg types
    __gsignals__: dict[str, tuple[GObject.SignalFlags, None, tuple[type, ...]]] = {
        'game-added':       (GObject.SignalFlags.RUN_FIRST, None, (GameItem,)),
        'game-unknown-exec':(GObject.SignalFlags.RUN_FIRST, None, (GameItem,)),
        'game-removed':     (GObject.SignalFlags.RUN_FIRST, None, (GameItem,)),
        'game-changed':     (GObject.SignalFlags.RUN_FIRST, None, (GameItem,)),
        # object=subprocess.Popen[bytes]
        'game-launched':    (GObject.SignalFlags.RUN_FIRST, None, (GameItem, object)),
        # bool=is_stderr
        'game-log':         (GObject.SignalFlags.RUN_FIRST, None, (GameItem, str, bool)),
        # bool=failed, object=Error | None
        'game-closed':      (GObject.SignalFlags.RUN_FIRST, None, (GameItem, bool, object)),
        'task-started':     (GObject.SignalFlags.RUN_FIRST, None, (RencherTask, object)),
        # object=Error | None
        'task-finished':    (GObject.SignalFlags.RUN_FIRST, None, (RencherTask, object)),
        'message':          (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__()
        self.store = Gio.ListStore(item_type=GameItem)
        self.tasks = {}
        self.processes = {}
        self._terminating_processes = []
        self._pool_generation = None
        self._thread_pool = ThreadPoolExecutor()

        self.action_group = Gio.SimpleActionGroup.new()
        # s = top_dir
        delete_action = Gio.SimpleAction.new_stateful('delete-game', GLib.VariantType.new('s'), GLib.Variant('d', 0.0))
        delete_action.connect('activate', self._on_delete_game)
        self.action_group.add_action(delete_action)
        # sss = top_dir, nickname, game top_dir
        import_action = Gio.SimpleAction.new_stateful('import-game', GLib.VariantType('(sss)'), GLib.Variant('d', 0.0))
        import_action.connect('activate', self._on_import_game)
        self.action_group.add_action(import_action)
        # s = top_dir
        run_action = Gio.SimpleAction.new('run-game', GLib.VariantType.new('s'))
        run_action.connect('activate', self._run_game)
        self.action_group.add_action(run_action)
        # s = top_dir
        stop_action = Gio.SimpleAction.new('stop-game', GLib.VariantType.new('s'))
        stop_action.connect('activate', self._close_game)
        self.action_group.add_action(stop_action)
        # s = uuid
        retry_action = Gio.SimpleAction.new('retry-task', GLib.VariantType.new('s'))
        retry_action.connect('activate', self._retry_task)
        self.action_group.add_action(retry_action)
        # s = uuid
        cancel_action = Gio.SimpleAction.new('cancel-task', GLib.VariantType.new('s'))
        cancel_action.connect('activate', self._cancel_task)
        self.action_group.add_action(cancel_action)

    def find(self, top_dir: str | Path) -> tuple[int, GameItem] | None:
        top_dir = os.path.normpath(top_dir)
        for game_item in self.store:
            if not game_item or not isinstance(game_item, GameItem):
                continue
            item_top_dir = os.path.normpath(game_item.top_dir)
            if top_dir == item_top_dir or top_dir.startswith(item_top_dir + os.sep):
                found, pos = self.store.find(game_item)
                if found:
                    return pos, game_item
        return None

    def load_games(self) -> None:
        data_dir = RencherConfig().get_data_dir()
        games_dir = Path(data_dir) / 'games'
        games_dir.mkdir(exist_ok=True, parents=True)
        logging.info(f'Loading games from "{data_dir}"')
        for item in list(self.store):
            if isinstance(item, GameItem):
                self.remove_game(item.top_dir)

        self._pool_generation = uuid.uuid4()
        gen = self._pool_generation

        for top_dir in games_dir.iterdir():
            self._thread_pool.submit(self._pool_add_game, str(top_dir), gen)

    def _msg(self, _t: RencherTask, text: str) -> None:
        self.emit('message', text)

    def _load_game(self, top_dir: str) -> tuple[GameItem | None, Exception | None]:
        game_item = None
        try:
            game_item = GameItem(top_dir=top_dir)
            game_item.game.get_main_script()
            return game_item, None
        except Exception as e:
            return game_item, e

    def _pool_add_game(self, top_dir: str, gen: uuid.UUID) -> None:
        if gen != self._pool_generation:
            return

        game_item = self._load_game(top_dir)

        def _finish() -> bool:
            if gen == self._pool_generation:
                self.add_game(top_dir, game_item)
            return GLib.SOURCE_REMOVE

        GLib.idle_add(_finish)

    def add_game(self, top_dir: str, pool_entry: tuple[GameItem | None, Exception | None] | None = None) -> None:
        if self.find(top_dir):
            self.update_game(top_dir)
            return

        game_item, error = pool_entry or self._load_game(top_dir)
        match error:
            case None:
                pass
            case GameNoExecutableError():
                if game_item:
                    self.emit('game-unknown-exec', game_item)
                return
            case GameInvalidError():
                logging.warning(f'Couldn\'t load "{os.path.basename(top_dir)}"')
                return
            case _:
                logging.error(f'Couldn\'t load "{os.path.basename(top_dir)}" because of {error}')
                return

        if game_item:
            self.store.append(game_item)
            self.emit('game-added', game_item)

            logging.debug(f'Added: "{os.path.basename(top_dir)}"')

    def remove_game(self, top_dir: str) -> None:
        result = self.find(top_dir)
        if result:
            i, item = result
            self.store.remove(i)
            self.emit('game-removed', item)
        logging.debug(f'Removed: "{os.path.basename(top_dir)}"')

    def update_game(self, top_dir: str) -> None:
        result = self.find(top_dir)
        if result:
            i, game_item = result
            game_item.update(game_item.game)
            self.store.items_changed(i, 1, 1)
            self.emit('game-changed', game_item)
        logging.debug(f'Changed: "{os.path.basename(top_dir)}"')

    def _task_started(self, task: RencherTask, game_item: GameItem | None = None):
        self.emit('task-started', task, game_item)
        self.tasks[str(task.uuid)] = task

    def _task_finished(self, task: RencherTask, game_item: GameItem | None = None):
        self.emit('task-finished', task, game_item)
        if not task.error and not task.warnings:
            self.tasks.pop(str(task.uuid), None)

    def _on_delete_game(self, _action: Gio.SimpleAction, parameter: GLib.Variant) -> None:
        top_dir = parameter.get_string()
        task = DeleteGameTask(top_dir)
        self._delete_game(task)

    def _delete_game(self, task: DeleteGameTask) -> None:
        if result := self.find(task.top_dir):
            self._task_started(task, result[1])

        def _on_finished(t: DeleteGameTask, _p: GObject.ParamSpec):
            try:
                game = Game(task.top_dir)
                if not game.validate():
                    self.remove_game(str(task.top_dir))
            except Exception:
                self.remove_game(str(task.top_dir))
            # self.emit('task-finished', t, None)
            self._task_finished(t)

        task.connect('message', self._msg)
        task.connect('notify::finished', _on_finished)
        task.start()

    def _on_import_game(self, _action: Gio.SimpleAction, parameter: GLib.Variant) -> None:
        file_path = parameter.get_child_value(0).get_string()
        nickname = parameter.get_child_value(1).get_string() or None
        game_top_dir = parameter.get_child_value(2).get_string()

        target_item = self.find(game_top_dir)
        task = ImportGameTask(Path(file_path), nickname, target_item[1] if target_item else None)
        self._import_game(task)

    def _import_game(self, task: ImportGameTask) -> None:
        # self.emit('task-started', task, None)
        self._task_started(task)

        def _on_finished(t: ImportGameTask, _p: GObject.ParamSpec):
            if t.game and t.game_path:
                game_item = GameItem(game=t.game)
                self.store.append(game_item)
                self.update_game(str(t.game_path))
                # self.emit('task-finished', t, entry)
                self._task_finished(t, game_item)
            else:
                # self.emit('task-finished', t, None)
                self._task_finished(t)

        task.connect('message', self._msg)
        task.connect('notify::finished', _on_finished)
        task.start()

    def _run_game(self, _action: Gio.SimpleAction, param: GLib.Variant) -> None:
        top_dir = param.get_string()
        if not (result := self.find(top_dir)):
            logging.error(f'No game found at "{top_dir}"')
            return
        game_item = result[1]
        if game_item in self.processes:
            logging.error(f'Game "{top_dir}" is already running')
            return

        logging.info(f'Launching "{top_dir}"...')

        try:
            process = game_item.run()
        except GameNoExecutableError as e:
            logging.error('Couldn\'t find the game\'s executable!')
            self.emit('game-closed', game_item, False, e)
            return
        except Exception as e:
            self.emit('game-closed', game_item, False, e)
            return
        else:
            if not process:
                return

        self.processes[game_item] = ((process, time.time()))
        self.emit('game-launched', game_item, process)

        for stream, is_stderr in [(process.stdout, False), (process.stderr, True)]:
            threading.Thread(target=self._read_stream, args=(game_item, stream, is_stderr), daemon=True).start()

        def _watch_process() -> bool:
            if process in self._terminating_processes:
                return GLib.SOURCE_REMOVE
            if process.poll() is not None:
                self._cleanup_game(game_item)
                return GLib.SOURCE_REMOVE
            return GLib.SOURCE_CONTINUE

        GLib.timeout_add(CHECK_PROCESS_MS, _watch_process)

    def is_game_running(self, top_dir: str) -> bool:
        result = self.find(top_dir)
        return result is not None and result[1] in self.processes

    def _read_stream(self, game_item: GameItem, stream: IO[bytes], is_stderr: bool) -> None:
        for line in stream:
            GLib.idle_add(self.emit, 'game-log', game_item, line.decode(errors='replace'), is_stderr)

    def _close_game(self, _action: Gio.SimpleAction, param: GLib.Variant) -> None:
        top_dir = param.get_string()
        if not (result := self.find(top_dir)):
            logging.error(f'No game found at "{top_dir}"')
            return
        game_item = result[1]
        if game_item not in self.processes:
            return

        logging.info(f'Closing "{top_dir}"...')

        process = self.processes[game_item][0]
        if process.poll() is not None:
            self._cleanup_game(game_item)
        else:
            process.terminate()

            if process not in self._terminating_processes:
                self._terminating_processes.append(process)

                def _wait_to_term() -> bool:
                    if process.poll() is not None:
                        self._cleanup_game(game_item)
                        return GLib.SOURCE_REMOVE
                    return GLib.SOURCE_CONTINUE

                GLib.timeout_add(CHECK_PROCESS_MS, _wait_to_term)

    def _cleanup_game(self, game_item: GameItem) -> None:
        if not (info := self.processes.pop(game_item, None)):
            return

        process, start = info
        failed = process.returncode != 0 and process not in self._terminating_processes

        if process in self._terminating_processes:
            self._terminating_processes.remove(process)

        game_item.game.cleanup(time.time() - start)

        self.emit('game-closed', game_item, failed, None)

    def _retry_task(self, _action: Gio.SimpleAction, uuid: GLib.Variant):
        uuid_str = uuid.get_string()
        if not (old_task := self.tasks.get(uuid_str, None)):
            return
        new_task = old_task.get_retry_task()
        if not new_task:
            return

        logging.debug(f'Retrying task {old_task.uuid}. Now is {new_task.uuid} - {new_task.label}')
        if isinstance(new_task, ImportGameTask):
            self._import_game(new_task)
        elif isinstance(new_task, DeleteGameTask):
            self._delete_game(new_task)

    def _cancel_task(self, _action: Gio.SimpleAction, uuid: GLib.Variant):
        # ugh
        uuid_str = uuid.get_string()
        if not (old_task := self.tasks.get(uuid_str, None)):
            return
        old_task.cancel()
        new_task = old_task.get_cancel_task()
        if not new_task:
            return

        logging.debug(f'Cancelling task {old_task.uuid}. Now is {new_task.uuid} - {new_task.label}')
        if isinstance(new_task, ImportGameTask):
            self._import_game(new_task)
        elif isinstance(new_task, DeleteGameTask):
            self._delete_game(new_task)
