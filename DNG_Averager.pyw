import tkinter as tk
from tkinter import filedialog, ttk
import numpy as np
import rawpy
from PIL import Image
import threading
import time
import subprocess
import os

def process_images(batch_size=10):
    def save_image(save_path, average_image):
        img_with_exif = Image.fromarray(np.uint8(average_image))
        img_with_exif.save(save_path)
        subprocess.run(["C:\Program Files (x86)\exiftool\exiftool.exe", "-tagsFromFile", file_paths[0], "-ExposureTime=" + str(total_exposure_time), save_path])
        os.remove(save_path + "_original")
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

    batch_images = []
    total_exposure_time = 0

    for index, file_path in enumerate(file_paths):
        with rawpy.imread(file_path) as raw:
            img = raw.postprocess()
            batch_images.append(img)

        exiftool_output = subprocess.check_output(["C:\Program Files (x86)\exiftool\exiftool.exe", "-ExposureTime", file_path])
        exposure_time = float(exiftool_output.decode("utf-8").strip().split(":")[-1].strip())
        total_exposure_time += exposure_time

        if (index + 1) % batch_size == 0 or (index + 1) == total_files:
            average_image = np.mean(batch_images, axis=0)
            threading.Thread(target=save_image, args=(save_path, average_image)).start()
            batch_images.clear()

            update_status(f"Processed {index + 1}/{total_files} images")

app = tk.Tk()
app.title("DNG Averager")

frame = ttk.Frame(app, padding="10 10 10 10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ttk.Label(frame, text="Select DNG files to average:").grid(row=0, column=0, sticky=tk.W)
ttk.Button(frame, text="Select files", command=process_images).grid(row=0, column=1, sticky=tk.E)

status_var = tk.StringVar()
status_label = ttk.Label(frame, textvariable=status_var)
status_label.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))

app.mainloop()
