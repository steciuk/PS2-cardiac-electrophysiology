import pickle
import tkinter as tk
from tkinter import filedialog


def pickle_data(data):
    root = tk.Tk()
    root.withdraw()

    path = filedialog.asksaveasfilename(filetypes=[("Pickle files", "*.pkl")])

    root.destroy()

    if path is None or len(path) == 0:
        return

    if not path.endswith(".pkl"):
        path += ".pkl"

    print("Saving to", path)
    with open(path, "wb") as f:
        pickle.dump(data, f)
        print("Export complete")
