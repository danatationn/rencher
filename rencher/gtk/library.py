import logging
import os.path
import subprocess
import time
from pathlib import Path

from gi.repository import Gio, GLib, GObject

from rencher.gtk.game_entry import GameEntry
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

    # this is all horrendous and will be refactored after v1.2.0

    action_group: Gio.SimpleActionGroup
    store: Gio.ListStore
    tasks: dict[str, RencherTask]  # str is uuid. tasks with errors stay
    processes: dict[GameEntry, tuple[subprocess.Popen[bytes], float]]  # float is time
    _terminating_processes: list[subprocess.Popen[bytes]]

    # signal name: flags, return types, arg types
    __gsignals__: dict[str, tuple[GObject.SignalFlags, None, tuple[type, ...]]] = {
        'game-added':       (GObject.SignalFlags.RUN_FIRST, None, (GameEntry,)),
        'game-unknown-exec':(GObject.SignalFlags.RUN_FIRST, None, (GameEntry,)),
        'game-removed':     (GObject.SignalFlags.RUN_FIRST, None, (GameEntry,)),
        'game-changed':     (GObject.SignalFlags.RUN_FIRST, None, (GameEntry,)),
        # object = subprocess.Popen[bytes]
        'game-launched':    (GObject.SignalFlags.RUN_FIRST, None, (GameEntry, object)),
        # object, object = subprocess.Popen[bytes] | None, Error | None
        'game-closed':      (GObject.SignalFlags.RUN_FIRST, None, (GameEntry, object, object)),
        'task-started':     (GObject.SignalFlags.RUN_FIRST, None, (RencherTask, object)),
        # object = Error | None
        'task-finished':    (GObject.SignalFlags.RUN_FIRST, None, (RencherTask, object)),
        'message':          (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__()
        self.store = Gio.ListStore(item_type=GameEntry)
        self.tasks = {}
        self.processes = {}
        self._terminating_processes = []

        self.action_group = Gio.SimpleActionGroup.new()
        # s = rpath
        delete_action = Gio.SimpleAction.new_stateful('delete-game', GLib.VariantType.new('s'), GLib.Variant('d', 0.0))
        delete_action.connect('activate', self._on_delete_game)
        self.action_group.add_action(delete_action)
        # sss = rpath, nickname, game rpath
        import_action = Gio.SimpleAction.new_stateful('import-game', GLib.VariantType('(sss)'), GLib.Variant('d', 0.0))
        import_action.connect('activate', self._on_import_game)
        self.action_group.add_action(import_action)
        # s = rpath
        run_action = Gio.SimpleAction.new('run-game', GLib.VariantType.new('s'))
        run_action.connect('activate', self._run_game)
        self.action_group.add_action(run_action)
        # s = rpath
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

    def find(self, rpath: str | Path) -> tuple[int, GameEntry] | None:
        rpath = os.path.normpath(rpath)
        for entry in self.store:
            if not entry or not isinstance(entry, GameEntry):
                continue
            item_rpath = os.path.normpath(entry.rpath)
            if rpath == item_rpath or rpath.startswith(item_rpath + os.sep):
                found, pos = self.store.find(entry)
                if found:
                    return pos, entry
        return None

    def load_games(self) -> None:
        data_dir = RencherConfig().get_data_dir()
        games_dir = Path(data_dir) / 'games'
        games_dir.mkdir(exist_ok=True, parents=True)
        logging.info(f'Loading games from "{data_dir}"')
        for item in list(self.store):
            if isinstance(item, GameEntry):
                self.remove_game(item.rpath)

        for dir in games_dir.iterdir():
            rpath = games_dir / dir
            GLib.idle_add(self.add_game, rpath)

    def _msg(self, _t: RencherTask, text: str) -> None:
        self.emit('message', text)

    def add_game(self, rpath: str) -> None:
        if self.find(rpath):
            self.update_game(rpath)
            return

        game_item = None

        try:
            game_item = GameEntry(rpath=rpath)
            game_item.game.get_main_script()
        except GameNoExecutableError:
            if game_item:
                self.emit('game-unknown-exec', game_item)
            return
        except GameInvalidError:
            logging.warning(f'Couldn\'t load "{os.path.basename(rpath)}"')
            return

        self.store.append(game_item)
        self.emit('game-added', game_item)

        logging.debug(f'Added: "{os.path.basename(rpath)}"')

    def remove_game(self, rpath: str) -> None:
        result = self.find(rpath)
        if result:
            i, item = result
            self.store.remove(i)
            self.emit('game-removed', item)
        logging.debug(f'Removed: "{os.path.basename(rpath)}"')

    def update_game(self, rpath: str) -> None:
        result = self.find(rpath)
        if result:
            i, game_item = result
            game_item.update(game_item.game)
            self.store.items_changed(i, 1, 1)
            self.emit('game-changed', game_item)
        logging.debug(f'Changed: "{os.path.basename(rpath)}"')

    def _task_started(self, task: RencherTask, entry: GameEntry | None = None):
        self.emit('task-started', task, entry)
        self.tasks[str(task.uuid)] = task

    def _task_finished(self, task: RencherTask, entry: GameEntry | None = None):
        self.emit('task-finished', task, entry)
        if not task.error and not task.warnings:
            self.tasks.pop(str(task.uuid), None)

    def _on_delete_game(self, _action: Gio.SimpleAction, parameter: GLib.Variant) -> None:
        rpath = parameter.get_string()
        task = DeleteGameTask(rpath)
        self._delete_game(task)

    def _delete_game(self, task: DeleteGameTask) -> None:
        if result := self.find(task.rpath):
            self._task_started(task, result[1])

        def _on_finished(t: DeleteGameTask, _p: GObject.ParamSpec):
            try:
                game = Game(task.rpath)
                if not game.validate():
                    self.remove_game(str(task.rpath))
            except Exception:
                self.remove_game(str(task.rpath))
            # self.emit('task-finished', t, None)
            self._task_finished(t)

        task.connect('message', self._msg)
        task.connect('notify::finished', _on_finished)
        task.start()

    def _on_import_game(self, _action: Gio.SimpleAction, parameter: GLib.Variant) -> None:
        file_path = parameter.get_child_value(0).get_string()
        nickname = parameter.get_child_value(1).get_string() or None
        game_rpath = parameter.get_child_value(2).get_string()

        target_entry = self.find(game_rpath)
        task = ImportGameTask(Path(file_path), nickname, target_entry[1] if target_entry else None)
        self._import_game(task)

    def _import_game(self, task: ImportGameTask) -> None:
        # self.emit('task-started', task, None)
        self._task_started(task)

        def _on_finished(t: ImportGameTask, _p: GObject.ParamSpec):
            if t.game and t.game_path:
                entry = GameEntry(game=t.game)
                self.store.append(entry)
                self.update_game(str(t.game_path))
                # self.emit('task-finished', t, entry)
                self._task_finished(t, entry)
            else:
                # self.emit('task-finished', t, None)
                self._task_finished(t)

        task.connect('message', self._msg)
        task.connect('notify::finished', _on_finished)
        task.start()

    def _run_game(self, _action: Gio.SimpleAction, param: GLib.Variant) -> None:
        rpath = param.get_string()
        if not (result := self.find(rpath)):
            logging.error(f'No game found at "{rpath}"')
            return
        entry = result[1]
        if entry in self.processes:
            logging.error(f'Game "{rpath}" is already running')
            return

        logging.info(f'Launching "{rpath}"...')

        try:
            process = entry.run()
        except GameNoExecutableError as e:
            logging.error('Couldn\'t find the game\'s executable!')
            self.emit('game-closed', entry, None, e)
            return
        except Exception as e:
            self.emit('game-closed', entry, None, e)
            return

        self.processes[entry] = ((process, time.time()))
        self.emit('game-launched', entry, process)

        def _watch_process() -> bool:
            if process in self._terminating_processes:
                return GLib.SOURCE_REMOVE
            if process.poll() is not None:
                self._cleanup_game(entry)
                return GLib.SOURCE_REMOVE
            return GLib.SOURCE_CONTINUE

        GLib.timeout_add(CHECK_PROCESS_MS, _watch_process)

    def _close_game(self, _action: Gio.SimpleAction, param: GLib.Variant) -> None:
        rpath = param.get_string()
        if not (result := self.find(rpath)):
            logging.error(f'No game found at "{rpath}"')
            return
        entry = result[1]
        if entry not in self.processes:
            return

        logging.info(f'Closing "{rpath}"...')

        process = self.processes[entry][0]
        if process.poll() is not None:
            self._cleanup_game(entry)
        else:
            process.terminate()

            if process not in self._terminating_processes:
                self._terminating_processes.append(process)

                def _wait_to_term() -> bool:
                    if process.poll() is not None:
                        self._cleanup_game(entry)
                        return GLib.SOURCE_REMOVE
                    return GLib.SOURCE_CONTINUE

                GLib.timeout_add(CHECK_PROCESS_MS, _wait_to_term)

    def _cleanup_game(self, entry: GameEntry) -> None:
        process, start = self.processes[entry]
        del self.processes[entry]

        entry.game.cleanup(time.time() - start)

        self.emit('game-closed', entry, process, None)

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
        logging.debug('mgrefhjkivnrevu4h74hfgiu4llgf')
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
