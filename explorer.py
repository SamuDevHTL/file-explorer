import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import platform
import json


class FileExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("File Explorer")
        self.create_widgets()
        self.populate_root()  # Populate the root directory when the application starts
        self.load_shortcuts()  # Load shortcuts when the application starts

        # Bind the close event to save shortcuts
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Create a frame for the entire interface
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Top path bar
        self.path_bar_frame = ttk.Frame(self.main_frame)
        self.path_bar_frame.pack(fill=tk.X)
        self.path_entry = ttk.Entry(self.path_bar_frame)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        self.go_button = ttk.Button(self.path_bar_frame, text="Go", command=self.navigate_to_path)
        self.go_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Split view: sidebar and main view
        self.split_frame = ttk.Frame(self.main_frame)
        self.split_frame.pack(fill=tk.BOTH, expand=True)

        # Sidebar for shortcuts
        self.sidebar = ttk.Treeview(self.split_frame, show="tree")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.sidebar.bind("<<TreeviewSelect>>", self.on_shortcut_select)

        # Add a context menu for the sidebar
        self.sidebar_context_menu = tk.Menu(self.root, tearoff=0)
        self.sidebar_context_menu.add_command(label="Remove Shortcut", command=self.remove_selected_shortcut)

        # Bind right-click event to the sidebar to show the context menu
        self.sidebar.bind("<Button-3>", self.show_sidebar_context_menu)  # For Windows/Linux

        # Main directory tree
        self.tree_frame = ttk.Frame(self.split_frame)
        self.tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(self.tree_frame, show="tree")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a scrollbar
        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Bind events for the directory tree
        self.tree.bind("<<TreeviewOpen>>", self.on_expand)
        self.tree.bind("<Double-1>", self.on_double_click)

        # Create a context menu for the tree view
        self.tree_context_menu = tk.Menu(self.root, tearoff=0)
        self.tree_context_menu.add_command(label="Add as Shortcut", command=self.add_selected_as_shortcut)

        # Bind right-click event to show the context menu
        self.tree.bind("<Button-3>", self.show_tree_context_menu)  # For Windows/Linux
        self.tree.bind("<Button-2>", self.show_tree_context_menu)  # For macOS

    def show_sidebar_context_menu(self, event):
        """Show the context menu for the sidebar."""
        item_id = self.sidebar.identify_row(event.y)
        if item_id:
            self.sidebar.selection_set(item_id)
            self.sidebar_context_menu.post(event.x_root, event.y_root)

    def remove_selected_shortcut(self):
        """Remove the selected shortcut from the sidebar."""
        selected_item = self.sidebar.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a shortcut to remove.")
            return

        item_id = selected_item[0]
        self.sidebar.delete(item_id)

    def navigate_to_path(self):
        """Navigate to the path entered in the path bar."""
        path = self.path_entry.get()
        if os.path.exists(path) and os.path.isdir(path):
            self.tree.delete(*self.tree.get_children())
            self.add_node("", path, path, is_dir=True)
            self.populate_tree(self.tree.get_children()[0])
        else:
            messagebox.showerror("Error", "Invalid Path")

    def populate_root(self):
        """Populate the tree with the root directory."""
        self.tree.delete(*self.tree.get_children())
        if platform.system() == "Windows":
            drives = [f"{chr(letter)}:\\" for letter in range(65, 91) if os.path.exists(f"{chr(letter)}:\\")]
            for drive in drives:
                self.add_node("", drive, drive, is_dir=True)
        else:
            root_path = "/"
            self.add_node("", root_path, root_path, is_dir=True)

    def add_node(self, parent, text, path, is_dir):
        """Add a node to the tree. If it's a directory, add a dummy child."""
        node_id = self.tree.insert(parent, "end", text=text, values=[path])
        if is_dir:
            self.tree.insert(node_id, "end")  # Add a dummy child to make it expandable

    def populate_tree(self, parent_id):
        """Populate the given tree node with its children."""
        node_path = self.tree.item(parent_id, "values")[0]
        self.tree.delete(*self.tree.get_children(parent_id))  # Clear dummy children
        try:
            for entry in os.scandir(node_path):
                self.add_node(
                    parent_id, entry.name, entry.path, is_dir=entry.is_dir()
                )
        except PermissionError:
            messagebox.showwarning("Permission Denied", f"Cannot access {node_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_expand(self, event):
        """Handle the expansion of a node."""
        node_id = self.tree.focus()
        if node_id:
            self.populate_tree(node_id)
            self.update_path_bar(node_id)

    def on_double_click(self, event):
        """Handle double-click: open files or expand directories."""
        node_id = self.tree.focus()
        if not node_id:
            return
        node_path = self.tree.item(node_id, "values")[0]
        if os.path.isdir(node_path):
            self.populate_tree(node_id)
            self.update_path_bar(node_id)
        elif os.path.isfile(node_path):
            self.open_file(node_path)

    def on_shortcut_select(self, event):
        """Navigate to a shortcut path."""
        node_id = self.sidebar.focus()
        if not node_id:
            return
        path = self.sidebar.item(node_id, "values")[0]
        if os.path.exists(path):
            self.tree.delete(*self.tree.get_children())
            self.add_node("", path, path, is_dir=True)
            self.populate_tree(self.tree.get_children()[0])
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def update_path_bar(self, node_id):
        """Update the path bar with the current directory path."""
        path = self.tree.item(node_id, "values")[0]
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, path)

    def open_file(self, path):
        """Open a file using the default application."""
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open file: {e}")

    def show_tree_context_menu(self, event):
        """Show the context menu on right-click."""
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.tree_context_menu.post(event.x_root, event.y_root)

    def add_selected_as_shortcut(self):
        """Add the selected folder in the tree view as a shortcut to the sidebar."""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        item_id = selected_item[0]
        item_path = self.tree.item(item_id, "values")[0]

        if os.path.isdir(item_path):
            folder_name = os.path.basename(item_path)
            self.sidebar.insert("", "end", text=folder_name, values=[item_path])
        else:
            messagebox.showwarning("Invalid Selection", "Please select a folder to add as a shortcut.")

    def save_shortcuts(self):
        """Save the shortcuts to a JSON file."""
        shortcuts = {}
        for item in self.sidebar.get_children():
            name = self.sidebar.item(item, "text")
            path = self.sidebar.item(item, "values")[0]
            shortcuts[name] = path

        json_file_path = os.path.join(os.path.dirname(__file__), "shortcuts.json")
        with open(json_file_path, "w") as file:
            json.dump(shortcuts, file)

    def load_shortcuts(self):
        """Load the shortcuts from a JSON file."""
        json_file_path = os.path.join(os.path.dirname(__file__), "shortcuts.json")
        if os.path.exists(json_file_path):
            with open(json_file_path, "r") as file:
                shortcuts = json.load(file)
                for name, path in shortcuts.items():
                    self.sidebar.insert("", "end", text=name, values=[path])

    def on_close(self):
        """Save shortcuts and close the application."""
        self.save_shortcuts()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = FileExplorer(root)
    root.geometry("900x600")
    root.mainloop()
