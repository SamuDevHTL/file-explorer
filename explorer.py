import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import platform


class FileExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("File Explorer")
        self.create_widgets()
        self.populate_root()

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

        # Add shortcuts
        self.add_shortcuts()

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

    def add_shortcuts(self):
        """Add common shortcuts to the sidebar."""
        shortcuts = {
            "Desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
            "Documents": os.path.join(os.path.expanduser("~"), "Documents"),
            "Downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
            "Home": os.path.expanduser("~"),
        }
        for name, path in shortcuts.items():
            self.sidebar.insert("", "end", text=name, values=[path])

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


if __name__ == "__main__":
    root = tk.Tk()
    app = FileExplorer(root)
    root.geometry("900x600")
    root.mainloop()
