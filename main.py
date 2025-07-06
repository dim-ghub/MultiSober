#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk
import os
import shutil
import subprocess
from pathlib import Path
import ast
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("Withdrawal")

INSTANCES_DIR = Path.home() / "Withdrawal" / "Instances"
INSTANCES_LIST = INSTANCES_DIR / "Instances.list"
APP_ID = "org.vinegarhq.Sober"

# Define the paths for the Sober configuration
SOBER_CONFIG_DIR = Path.home() / ".var" / "app" / APP_ID / "config" / "sober"
SOBER_CONFIG_FILE = SOBER_CONFIG_DIR / "config.json"

class InstanceAlreadyExist(Exception):
    pass

class WithdrawalManager:
    def __init__(self):
        INSTANCES_DIR.mkdir(parents=True, exist_ok=True)

    def add_instance(self, name):
        path = INSTANCES_DIR / name
        if path.exists():
            raise InstanceAlreadyExist(f"Instance '{name}' already exists.")
        path.mkdir()
        self.update_instances_list(name)
        log.info(f"Created instance '{name}'")

    def update_instances_list(self, name):
        instances = self.list_instances()
        if name not in instances:
            instances.append(name)
            with open(INSTANCES_LIST, "w") as f:
                f.write(str(instances))

    def list_instances(self):
        if INSTANCES_LIST.exists():
            with open(INSTANCES_LIST, "r") as f:
                content = f.read().strip()
                return ast.literal_eval(content) if content else []
        return []

    def delete_instance(self, name):
        path = INSTANCES_DIR / name
        if not path.exists():
            return
        shutil.rmtree(path)
        instances = self.list_instances()
        if name in instances:
            instances.remove(name)
            with open(INSTANCES_LIST, "w") as f:
                f.write(str(instances))
        log.info(f"Deleted instance '{name}'")

    def rename_instance(self, old_name, new_name):
        old_path = INSTANCES_DIR / old_name
        new_path = INSTANCES_DIR / new_name
        if new_path.exists():
            raise InstanceAlreadyExist(f"Instance '{new_name}' already exists.")
        old_path.rename(new_path)
        instances = self.list_instances()
        if old_name in instances:
            idx = instances.index(old_name)
            instances[idx] = new_name
            with open(INSTANCES_LIST, "w") as f:
                f.write(str(instances))
        log.info(f"Renamed instance '{old_name}' to '{new_name}'")

    def run_instance(self, name):
        envpath = INSTANCES_DIR / name
        if not envpath.exists():
            envpath.mkdir(parents=True)
        
        log.info(f"Launching instance '{name}'")
        
        # Detach the child process using preexec_fn=os.setsid
        # This makes the child a session leader, so it won't be terminated when the parent exits.
        try:
            subprocess.Popen(
                ["env", f"HOME={envpath}", "flatpak", "run", APP_ID],
                preexec_fn=os.setsid, # This is the key for detaching on Unix-like systems
                stdout=subprocess.DEVNULL, # Redirect stdout to /dev/null
                stderr=subprocess.DEVNULL, # Redirect stderr to /dev/null
                stdin=subprocess.DEVNULL    # Redirect stdin to /dev/null
            )
            log.info(f"Instance '{name}' launched successfully and detached.")
        except Exception as e:
            log.error(f"Failed to launch instance '{name}': {e}")
            # You might want to show an error dialog here in the GUI
            # For simplicity, I'm just logging it for now.

class InstanceRow(Gtk.ListBoxRow):
    def __init__(self, name, manager, refresh_cb, run_cb):
        super().__init__()
        self.name = name
        self.manager = manager
        self.refresh_cb = refresh_cb
        self.run_cb = run_cb
        self.editing = False

        self.set_child(self._build_row())

    def _build_row(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, margin_top=6, margin_bottom=6, margin_start=6, margin_end=6)
        self.label = Gtk.Label(label=self.name, xalign=0)
        self.label.set_hexpand(True)

        self.import_button = Gtk.Button(label="Import Settings")
        self.edit_button = Gtk.Button(label="Edit")
        self.delete_button = Gtk.Button(label="Delete")
        self.run_button = Gtk.Button(label="Run")

        self.import_button.connect("clicked", self.on_import_clicked)
        self.edit_button.connect("clicked", self.on_edit_clicked)
        self.delete_button.connect("clicked", self.on_delete_clicked)
        self.run_button.connect("clicked", self.on_run_clicked)

        self.main_box.append(self.label)
        self.main_box.append(self.import_button)
        self.main_box.append(self.edit_button)
        self.main_box.append(self.delete_button)
        self.main_box.append(self.run_button)

        return self.main_box

    def on_import_clicked(self, button):
        source_file = SOBER_CONFIG_FILE
        destination_dir = INSTANCES_DIR / self.name / ".var" / "app" / APP_ID / "config" / "sober"
        destination_file = destination_dir / "config.json"

        if not source_file.exists():
            self.show_error(f"Source config file not found: {source_file}")
            log.warning(f"Source config file not found: {source_file}")
            return

        try:
            destination_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, destination_file)
            dialog = Gtk.MessageDialog(
                transient_for=self.get_root(),
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.CLOSE,
                text=f"Settings imported successfully for '{self.name}'."
            )
            dialog.connect("response", lambda d, r: d.destroy())
            dialog.present()
            log.info(f"Imported settings for instance '{self.name}' from '{source_file}' to '{destination_file}'")
        except FileNotFoundError as e:
            self.show_error(f"Error importing settings: {e}. Ensure the instance directory exists.")
            log.error(f"Error during import for '{self.name}': {e}")
        except Exception as e:
            self.show_error(f"An unexpected error occurred during import: {e}")
            log.error(f"Unexpected error during import for '{self.name}': {e}")

    def on_edit_clicked(self, button):
        if self.editing:
            return
        self.editing = True

        self.entry = Gtk.Entry()
        self.entry.set_text(self.name)
        self.save_button = Gtk.Button(label="Save")
        self.cancel_button = Gtk.Button(label="Cancel")

        self.main_box.remove(self.label)
        self.main_box.remove(self.import_button)
        self.main_box.remove(self.edit_button)
        self.main_box.remove(self.delete_button)
        self.main_box.remove(self.run_button)

        self.main_box.append(self.entry)
        self.main_box.append(self.save_button)
        self.main_box.append(self.cancel_button)

        self.save_button.connect("clicked", self.on_save_clicked)
        self.cancel_button.connect("clicked", self.on_cancel_clicked)

    def on_save_clicked(self, button):
        new_name = self.entry.get_text().strip()
        if not new_name:
            self.show_error("Name cannot be empty")
            return
        try:
            self.manager.rename_instance(self.name, new_name)
            self.name = new_name
            self.refresh_cb()
        except InstanceAlreadyExist as e:
            self.show_error(str(e))
        self.editing = False

    def on_cancel_clicked(self, button):
        self.editing = False
        self.refresh_cb()

    def on_delete_clicked(self, button):
        dialog = Gtk.MessageDialog(
            transient_for=self.get_root(),
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f"Delete instance '{self.name}'?"
        )
        dialog.connect("response", lambda d, response: self._handle_delete_response(d, response))
        dialog.present()

    def _handle_delete_response(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            self.manager.delete_instance(self.name)
            self.refresh_cb()
        dialog.destroy()


    def on_run_clicked(self, button):
        self.run_cb(self.name)

    def show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self.get_root(),
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text=message
        )
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.present()


class WithdrawalWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Withdrawal Manager")
        self.set_default_size(600, 400)
        self.manager = WithdrawalManager()

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        self.set_child(self.vbox)

        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_hexpand(True)
        self.scrolled_window.set_vexpand(True)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.scrolled_window.set_child(self.list_box)
        self.vbox.append(self.scrolled_window)

        self.add_button = Gtk.Button(label="Add Instance")
        self.add_button.connect("clicked", self.on_add_instance_clicked)
        self.vbox.append(self.add_button)

        self.refresh_instances()

    def refresh_instances(self):
        children = []
        child = self.list_box.get_first_child()
        while child is not None:
            children.append(child)
            child = child.get_next_sibling()
        for child in children:
            self.list_box.remove(child)

        instances = self.manager.list_instances()
        for name in instances:
            row = InstanceRow(name, self.manager, self.refresh_instances, self.run_instance)
            self.list_box.append(row)

    def on_add_instance_clicked(self, button):
        dialog = Gtk.Dialog(title="Add Instance", transient_for=self, modal=True)
        dialog.set_default_size(300, 100)
        content_area = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_placeholder_text("Enter instance name")
        content_area.append(entry)

        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Add", Gtk.ResponseType.OK)

        def handle_response(d, response):
            if response == Gtk.ResponseType.OK:
                name = entry.get_text().strip()
                if not name:
                    self.show_error("Instance name cannot be empty.")
                    return
                try:
                    self.manager.add_instance(name)
                    self.refresh_instances()
                    d.destroy()
                except InstanceAlreadyExist as e:
                    self.show_error(str(e))
            elif response == Gtk.ResponseType.CANCEL:
                d.destroy()

        dialog.connect("response", handle_response)
        dialog.present()

    def run_instance(self, name):
        self.manager.run_instance(name)

    def show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text=message,
        )
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.present()

class WithdrawalApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.dim.Withdrawal")

    def do_activate(self):
        win = WithdrawalWindow(self)
        win.present()

def main():
    app = WithdrawalApp()
    return app.run()

if __name__ == "__main__":
    main()
