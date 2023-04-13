import tkinter as tk
from tkinter import filedialog, ttk
import numpy as np
import rawpy
from PIL import Image
import threading
import time

def process_images():
    def save_image(save_path, average_image):
        Image.fromarray(np.uint8(average_image)).save(save_path)
        update_status("Averaged image saved successfully.")

    def update_status(message):
        status_var.set(message)
        status_label.update()

    file_paths = filedialog.askopenfilenames(title="Select .dng files", filetypes=[("DNG files", "*.dng")])

    if not file_paths:
        return

    save_path = filedialog.asksaveasfilename(title="Save as", defaultextension=".tiff", filetypes=[("TIFF files", "*.tiff"), ("JPEG files", "*.jpg"), ("PNG files", "*.png")])

    if not save_path:
        return

    total_files = len(file_paths)

    update_status("Starting to process images...")

    average_image = None
    count = 0

    for file_path in file_paths:
        try:
            with rawpy.imread(file_path) as raw:
                img = raw.postprocess().astype(np.float32)

            if average_image is None:
                average_image = img
            else:
                average_image += img

            count += 1
            progress = count / total_files * 100
            update_status(f"Processed image {count}/{total_files} ({progress:.2f}% completed)")
            progress_var.set(progress)
            progress_bar.update()

        except Exception as e:
            update_status(f"Error processing image {count}/{total_files}: {e}")
            continue

    average_image /= count

    update_status("Saving the averaged image...")
    save_thread = threading.Thread(target=save_image, args=(save_path, average_image))
    save_thread.start()

    while save_thread.is_alive():
        update_status("Saving in progress...")
        time.sleep(1)

def on_start_button_click():
    threading.Thread(target=process_images, daemon=True).start()

# Create the main window
root = tk.Tk()
root.title("Image Averager")
#root.geometry("400x200")

# Create the widgets
start_button = ttk.Button(root, text="Start", command=on_start_button_click)
status_var = tk.StringVar()
status_label = ttk.Label(root, textvariable=status_var, wraplength=300)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)

# Position the widgets
start_button.grid(row=0, column=0, padx=10, pady=10)
status_label.grid(row=1, column=0, padx=10, pady=10)
progress_bar.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

root.mainloop()
