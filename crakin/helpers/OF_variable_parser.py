# -*- coding: utf-8 -*-

import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog

def foam_list(file_path):
    try:
        out = subprocess.check_output(
            ["foamDictionary", file_path, "-list"],
            stderr=subprocess.STDOUT
        )
        return sorted(set(out.decode().split()))
    except:
        return []

def foam_value(file_path, key):
    try:
        out = subprocess.check_output(
            ["foamDictionary", file_path, "-entry", key, "-value"],
            stderr=subprocess.STDOUT
        )
        return out.decode().strip()
    except:
        return None



class OFExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenFOAM Case Explorer")

        self.case_path = None

        # Layout
        self.left = ttk.Frame(root)
        self.left.pack(side="left", fill="y")

        self.right = ttk.Frame(root)
        self.right.pack(side="right", fill="both", expand=True)

        # Tree
        self.tree = ttk.Treeview(self.left)
        self.tree.pack(fill="y", expand=True)

        self.tree.bind("<<TreeviewOpen>>", self.expand_node)
        self.tree.bind("<<TreeviewSelect>>", self.show_value)

        # Output
        self.text = tk.Text(self.right)
        self.text.pack(fill="both", expand=True)

        # Search
        self.search = tk.Entry(self.left)
        self.search.pack(fill="x")

        tk.Button(self.left, text="Search", command=self.search_case).pack(fill="x")
        tk.Button(self.left, text="Load Case", command=self.load_case).pack(fill="x")

    # ----------------------------
    # Load case folder
    # ----------------------------
    def load_case(self):
        path = filedialog.askdirectory()
        if not path:
            return

        self.case_path = path
        self.tree.delete(*self.tree.get_children())

        for item in os.listdir(path):
            full = os.path.join(path, item)
            node = self.tree.insert("", "end", text=item, values=(full,))
            if os.path.isdir(full):
                self.tree.insert(node, "end", text="loading...")

    # ----------------------------
    # Expand tree dynamically
    # ----------------------------
    def expand_node(self, event):
        node = self.tree.focus()
        path = self.get_path(node)

        # prevent duplicate expansion
        if self.tree.get_children(node):
            self.tree.delete(*self.tree.get_children(node))

        if os.path.isdir(path):
            for item in os.listdir(path):
                full = os.path.join(path, item)
                child = self.tree.insert(node, "end", text=item, values=(full,))
                if os.path.isdir(full):
                    self.tree.insert(child, "end", text="loading...")

        else:
            # OpenFOAM dictionary expansion
            keys = foam_list(path)
            for k in keys:
                self.tree.insert(node, "end", text=k, values=(f"{path}:{k}",))

    # ----------------------------
    # Get full path from node
    # ----------------------------
    def get_path(self, node):
        parts = []
        while node:
            parts.append(self.tree.item(node)["text"])
            node = self.tree.parent(node)
        parts.reverse()
        return os.path.join(*parts)

    # ----------------------------
    # Show value
    # ----------------------------
    def show_value(self, event):
        node = self.tree.focus()
        path = self.get_path(node)

        if ":" in path:
            file_path, key = path.split(":", 1)
            value = foam_value(file_path, key)

            self.text.delete("1.0", tk.END)
            self.text.insert(tk.END, f"{key}:\n{value}")

    # ----------------------------
    # Recursive search
    # ----------------------------
    def search_case(self):
        query = self.search.get().strip()
        if not self.case_path or not query:
            return

        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, f"Searching for: {query}\n\n")

        for root_dir, _, files in os.walk(self.case_path):
            for f in files:
                path = os.path.join(root_dir, f)
                try:
                    keys = foam_list(path)
                    if query in keys:
                        val = foam_value(path, query)
                        self.text.insert(tk.END, f"{path}\n{val}\n\n")
                except:
                    continue


# ----------------------------
# Run
# ----------------------------
root = tk.Tk()
app = OFExplorer(root)
root.mainloop()

