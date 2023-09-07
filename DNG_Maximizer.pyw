import tkinter as tk
from tkinter import filedialog, ttk
import numpy as np
import rawpy
from PIL import Image, ImageTk
import threading
import subprocess
import os
import queue
import concurrent.futures
import psutil
import sys
import os

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
exiftool_path = os.path.join(script_directory, "exiftool.exe")

message_queue = queue.Queue()

def process_single_image(file_path):
    with rawpy.imread(file_path) as raw:
        img = raw.postprocess()
    return img

def update_preview_image(img_array):
    img = Image.fromarray(np.uint8(img_array))
    img.thumbnail((600, 600))
    img_tk = ImageTk.PhotoImage(img)
    preview_image_label.config(image=img_tk)
    preview_image_label.image = img_tk

def restart_application():
    global stop_process
    stop_process = False
    restart_button.grid_remove()
    select_files_button.grid()
    files_label.grid()
    status_label.grid_remove()
    progress_bar.grid_remove()
    details_label.grid_remove()
    preview_image_label.grid_remove()
    status_var.set("")

def process_images_thread():
    def save_image(save_path, max_image):
        if max_image is None:
            message_queue.put(("status", "Error: No images were processed."))
            message_queue.put(("done",))
            return

        try:
            img_with_exif = Image.fromarray(np.uint8(max_image))
            img_with_exif.save(save_path)
            subprocess.run([exiftool_path, "-tagsFromFile", file_paths[0], "-ExposureTime=" + str(total_exposure_time), save_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            os.remove(save_path + "_original")
            message_queue.put(("status", "Maximizedd image saved successfully."))
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
    stop_process = False
    max_image = None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for index, file_path in enumerate(file_paths):
            try:
                img = process_single_image(file_path)
                if index == 0:
                    max_image = img                
                else:
                    max_image = np.maximum(max_image, img)
                    if index % 5 == 0:
                        message_queue.put(("update_preview_image", max_image))


                exiftool_output = subprocess.check_output([exiftool_path, "-ExposureTime", file_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                exposure_time = float(exiftool_output.decode("utf-8").strip().split(":")[-1].strip())
                total_exposure_time += exposure_time

                message_queue.put(("progress", index + 1, total_files))
                message_queue.put(("status", f"Processed {index + 1}/{total_files} images"))

                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                details_var.set(f"Batch size: {batch_size}\nThreads: {os.cpu_count()}\nCPU utilization: {cpu_percent}%\nMemory utilization: {memory_percent}%")

                if stop_process:
                    message_queue.put(("status", "Process stopped by the user"))
                    break

            except subprocess.CalledProcessError as e:
                message_queue.put(("status", "Error while reading EXIF data: " + str(e)))
                message_queue.put(("done",))
                return

    if not stop_process:
        save_image(save_path, max_image)
        message_queue.put(("progress", total_files, total_files))
        message_queue.put(("done",))

def process_images():
    select_files_button.grid_remove()
    stop_button.grid()
    files_label.grid_remove()
    status_label.grid()
    progress_bar.grid()
    details_label.grid()
    preview_image_label.grid()
    threading.Thread(target=process_images_thread).start()

def stop_process():
    global stop_process
    stop_process = True

def update_ui():
    try:
        message, *args = message_queue.get(block=False)
        if message == "status":
            status_var.set(args[0])
        elif message == "progress":
            progress_var.set(args[0])
            progress_bar.configure(maximum=args[1])
        elif message == "done":
            stop_button.grid_remove()
            select_files_button.grid()
            files_label.grid()
            status_label.grid_remove()
            progress_bar.grid_remove()
            details_label.grid_remove()
            preview_image_label.grid_remove()
            app.bell()
            status_var.set("Finished!")
        elif message == "update_preview_image":
            update_preview_image(args[0])
        elif message == "restart":
            restart_button.grid()

    except queue.Empty:
        pass

    app.after(100, update_ui)

app = tk.Tk()
app.title("DNG Maximizer")
app.configure(bg='#f0f0f0')

frame = ttk.Frame(app, padding="20 20 20 20")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

title_font = ('Arial', 14, 'bold')
label_font = ('Arial', 12)

title_label = ttk.Label(frame, text="DNG Maximizer", font=title_font)
title_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))

files_label = ttk.Label(frame, text="Select DNG files to Maximizer:", font=label_font)
files_label.grid(row=1, column=0, sticky=tk.W, padx=(10, 0))
select_files_button = ttk.Button(frame, text="Select files", command=process_images)
select_files_button.grid(row=1, column=1, sticky=tk.E, padx=(0, 10))

status_var = tk.StringVar()
status_label= ttk.Label(frame, textvariable=status_var, font=label_font)
status_label.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(10, 0), pady=(20, 0))

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(frame, variable=progress_var, mode='determinate')
progress_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(10, 10), pady=(10, 0))

details_var = tk.StringVar()
details_label = ttk.Label(frame, textvariable=details_var, font=label_font, wraplength=400, justify=tk.LEFT)
details_label.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(10, 0), pady=(20, 0))

preview_image_label = ttk.Label(frame)
preview_image_label.grid(row=5, column=0, columnspan=2, padx=(10, 10), pady=(20, 0))

stop_button = ttk.Button(frame, text="Stop", command=stop_process)
stop_button.grid(row=1, column=1, sticky=tk.E, padx=(0, 10))

restart_button = ttk.Button(frame, text="Restart", command=restart_application)
restart_button.grid(row=1, column=1, sticky=tk.E, padx=(0, 10))

status_label.grid_remove()
progress_bar.grid_remove()
details_label.grid_remove()
preview_image_label.grid_remove()
stop_button.grid_remove()
restart_button.grid_remove()

app.after(100, update_ui)
app.mainloop()


