import tkinter as tk
from tkinter import filedialog, ttk
import numpy as np
import rawpy
from PIL import Image
import threading
import time
import exifread
from fractions import Fraction

def process_images(batch_size=10):
    def save_image(save_path, average_image):
        Image.fromarray(np.uint8(average_image)).save(save_path)
        update_status("Averaged image saved successfully.")

    def update_status(message):
        status_var.set(message)
        status_label.update()

    file_paths = filedialog.askopenfilenames(title="Select .dng files", filetypes=[("DNG files", "*.dng")])

    if not file_paths:
        return

    save_path = filedialog.asksaveasfilename(title="Save as", defaultextension=".tiff", filetypes=[("TIFF files", "*.tiff")])

    if not save_path:
        return

    total_files = len(file_paths)

    update_status("Starting to process images...")

    total_exposure_time = 0

    for i in range(0, total_files, batch_size):
        batch_paths = file_paths[i:i+batch_size]
        batch_images = []

        for index, file_path in enumerate(batch_paths):
            with rawpy.imread(file_path) as raw:
                img = raw.postprocess()
                batch_images.append(img)

            progress = (i + index + 1) / total_files * 100
            update_status(f"Processed image {i + index + 1}/{total_files} ({progress:.2f}% completed)")

            # Read EXIF data and sum exposure times
            if index == 0:
                with open(file_path, "rb") as f:
                    tags = exifread.process_file(f)
                    exposure_time_tag = "EXIF ExposureTime"
                    exposure_time = Fraction(tags[exposure_time_tag].values[0])
                    total_exposure_time += exposure_time

        batch_stacked_image = np.stack(batch_images, axis=0)
        if i == 0:
            stacked_image = batch_stacked_image
        else:
            stacked_image = np.concatenate((stacked_image, batch_stacked_image), axis=0)

    average_image = np.mean(stacked_image, axis=0)

    update_status("Saving the averaged image as a TIFF file...")

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

# Create the widgets
start_button = ttk.Button(root, text="Start", command=on_start_button_click)
status_var = tk.StringVar()
status_label = ttk.Label(root, textvariable=status_var, wraplength=300)

# Position the widgets
start_button.grid(row=0, column=0, padx=10, pady=10)
status_label.grid(row=1, column=0, padx=10, pady=10)

root.mainloop()
