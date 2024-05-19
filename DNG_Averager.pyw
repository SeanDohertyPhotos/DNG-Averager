import tkinter as tk
from tkinter import filedialog, ttk
import numpy as np
import rawpy
from PIL import Image, ImageTk, ExifTags
import threading
import subprocess
import os
import queue
import psutil
import sys
from fractions import Fraction

# Get the script directory and the path to exiftool
script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
exiftool_path = os.path.join(script_directory, "exiftool.exe")

# Queue for inter-thread communication
result_queue = queue.Queue()

def process_image(file_path, index, total_files):
    """Process a single image file and return the result."""
    exposure_time = 0
    with rawpy.imread(file_path) as raw:
        img = raw.postprocess().astype(np.float32)
    with Image.open(file_path) as image:
        img_exif = image.getexif()
        for (k,v) in img_exif.items():
            if ExifTags.TAGS.get(k) == 'ExposureTime':
                exposure_time = v
    result_queue.put((index, img, exposure_time))
    progress_var.set(index + 1)
    status_var.set(f"Processed image {index + 1}/{total_files}")
    app.update_idletasks()  # Update the UI

def update_preview_image(average_image_array):
    """Update the preview image in the UI."""
    img = Image.fromarray(np.uint8(average_image_array))
    img.thumbnail((600, 600))
    img_tk = ImageTk.PhotoImage(img)
    preview_image_label.config(image=img_tk)
    preview_image_label.image = img_tk

def process_images_thread(file_paths, save_path):
    """Process the selected images into the queue"""
    total_files = len(file_paths)

    for index, file_path in enumerate(file_paths):
        process_image(file_path, index, total_files)
        
def average_images_thread(file_paths, save_path):
    """Average queued images"""
    total_files = len(file_paths)
    total_exposure_time = 0
    average_image = None
    processed_count = 0
    while processed_count < total_files:
        try:
            index, img, exposure_time = result_queue.get(timeout=0.1)
            processed_count += 1
            total_exposure_time += exposure_time

            if average_image is None:
                average_image = img
            else:
                average_image = (average_image * index + img) / (index + 1)

            if processed_count % 100 == 0 or processed_count == total_files:
                update_preview_image(average_image)

            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            details_var.set(f"Threads: {os.cpu_count()}\nCPU utilization: {cpu_percent}%\nMemory utilization: {memory_percent}%")

        except queue.Empty:
            pass

    # Save the averaged image with EXIF data
    average_image = np.clip(average_image, 0, 255).astype(np.uint8)
    img = Image.fromarray(average_image)
    img_exif = img.getexif()
    # 33434 exif ExposureTime numerical code
    img_exif[33434] = total_exposure_time
    img.save(save_path, exif=img_exif)

    status_var.set("Finished!")
    app.bell()

def process_images():
    """Process the selected images."""
    file_paths = filedialog.askopenfilenames(title="Select .dng files", filetypes=[("DNG files", "*.dng")])
    if not file_paths:
        status_var.set("No files selected.")
        return

    save_path = filedialog.asksaveasfilename(title="Save as", defaultextension=".tiff", filetypes=[("TIFF files", "*.tiff")])
    if not save_path:
        status_var.set("No save path specified.")
        return

    status_var.set("Starting to process images...")
    progress_var.set(0)
    progress_bar.config(maximum=len(file_paths))

    threads = [
    threading.Thread(target=process_images_thread, args=(file_paths, save_path)),
    threading.Thread(target=average_images_thread, args=(file_paths, save_path)),
    ]

    for t in threads:
        t.start()

app = tk.Tk()
app.title("DNG Averager")
app.configure(bg='#f0f0f0')

frame = ttk.Frame(app, padding="20 20 20 20")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

title_font = ('Arial', 14, 'bold')
label_font = ('Arial', 12)

title_label = ttk.Label(frame, text="DNG Averager", font=title_font)
title_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))

files_label = ttk.Label(frame, text="Select DNG files to average:", font=label_font)
files_label.grid(row=1, column=0, sticky=tk.W, padx=(10, 0))
select_files_button = ttk.Button(frame, text="Select files", command=process_images)
select_files_button.grid(row=1, column=1, sticky=tk.E, padx=(0, 10))

status_var = tk.StringVar()
status_label = ttk.Label(frame, textvariable=status_var, font=label_font)
status_label.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(10, 0), pady=(20, 0))

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(frame, variable=progress_var, mode='determinate')
progress_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(10, 10), pady=(10, 0))

details_var = tk.StringVar()
details_label = ttk.Label(frame, textvariable=details_var, font=label_font, wraplength=400, justify=tk.LEFT)
details_label.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(10, 0), pady=(20, 0))

preview_image_label = ttk.Label(frame)
preview_image_label.grid(row=5, column=0, columnspan=2, padx=(10, 10), pady=(20, 0))

app.mainloop()
