import tkinter as tk
from tkinter import filedialog, ttk
import numpy as np
import rawpy
from PIL import Image
import threading
import subprocess
import os
import queue
import concurrent.futures
import psutil

exiftool_path = "C:\\Program Files (x86)\\exiftool\\exiftool.exe"
message_queue = queue.Queue()

def process_single_image(file_path):
    with rawpy.imread(file_path) as raw:
        img = raw.postprocess()
    return img

def process_images_thread():
    def save_image(save_path, average_image):
        try:
            img_with_exif = Image.fromarray(np.uint8(average_image))
            img_with_exif.save(save_path)
            subprocess.run([exiftool_path, "-tagsFromFile", file_paths[0], "-ExposureTime=" + str(total_exposure_time), save_path])
            os.remove(save_path + "_original")
            message_queue.put(("status", "Averaged image saved successfully."))
        except Exception as e:
            message_queue.put(("status", "Error while saving the image: " + str(e)))

    try:
        file_paths = filedialog.askopenfilenames(title="Select .dng files", filetypes=[("DNG files", "*.dng")])
    except Exception as e:
        message_queue.put(("status", "Error while selecting files: " + str(e)))
        message_queue.put(("done",))
        return

    if not file_paths:
        message_queue.put(("status", "No files selected."))
        message_queue.put(("done",))
        return

    try:
        save_path = filedialog.asksaveasfilename(title="Save as", defaultextension=".tiff", filetypes=[("TIFF files", "*.tiff")])
    except Exception as e:
        message_queue.put(("status", "Error while specifying save path: " + str(e)))
        message_queue.put(("done",))
        return

    if not save_path:
        message_queue.put(("status", "No save path specified."))
        message_queue.put(("done",))
        return

    total_files = len(file_paths)
    message_queue.put(("status", "Starting to process images..."))

    batch_size = max(1, min(total_files // 4, os.cpu_count()))
    total_exposure_time = 0

    with concurrent.futures.ThreadPoolExecutor() as executor:
        images = list(executor.map(process_single_image, file_paths))
        average_image = np.mean(images, axis=0)

        for index, file_path in enumerate(file_paths):
            try:
                exiftool_output = subprocess.check_output([exiftool_path, "-ExposureTime", file_path])
                exposure_time = float(exiftool_output.decode("utf-8").strip().split(":")[-1].strip())
                total_exposure_time += exposure_time

                message_queue.put(("progress", index + 1, total_files))
                message_queue.put(("status", f"Processed {index + 1}/{total_files} images"))

                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                details_var.set(f"Batch size: {batch_size}\nThreads: {os.cpu_count()}\nCPU utilization: {cpu_percent}%\nMemory utilization: {memory_percent}%")

            except subprocess.CalledProcessError as e:
                message_queue.put(("status", "Error while reading EXIF data: " + str(e)))
                message_queue.put(("done",))
                return

    save_image(save_path, average_image)
    message_queue.put(("progress", total_files, total_files))
    message_queue.put(("done",))

def process_images():
    select_files_button.grid_remove()
    files_label.grid_remove()
    status_label.grid()
    progress_bar.grid()
    details_label.grid()
    threading.Thread(target=process_images_thread).start()

def update_ui():
    try:
        message, *args = message_queue.get(block=False)
        if message == "status":
            status_var.set(args[0])
        elif message == "progress":
            progress_var.set(args[0])
            progress_bar.configure(maximum=args[1])
        elif message == "done":
            select_files_button.grid()
            files_label.grid()
            status_label.grid_remove()
            progress_bar.grid_remove()
            details_label.grid_remove()
    except queue.Empty:
        pass

    app.after(100, update_ui)

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

status_label.grid_remove()
progress_bar.grid_remove()
details_label.grid_remove()

app.after(100, update_ui)
app.mainloop()

