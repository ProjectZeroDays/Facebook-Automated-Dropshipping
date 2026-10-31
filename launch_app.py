#!/usr/bin/env python3
"""Desktop launcher with mandatory legal disclaimer — restricted use only."""
import tkinter as tk
from tkinter import messagebox
import webbrowser, os

def main():
    root = tk.Tk()
    root.withdraw()
    result = messagebox.showwarning(
        "RESTRICTED LICENSE — ACKNOWLEDGE BEFORE USE",
        "PROPRIETARY RESTRICTED LICENSE — AUTHORIZED USE ONLY.\n"
        "Unauthorized use, redistribution, editing, or modification is PROHIBITED.\n"
        "All rights reserved to Authenticated, Inc. — Trey A. Smith.\n\n"
        "By clicking OK you acknowledge these restrictions."
    )
    if result == "ok":
        url = os.getenv("DASH_URL", "http://localhost:8080/")
        webbrowser.open(url)
    root.destroy()

if __name__ == "__main__":
    main()
