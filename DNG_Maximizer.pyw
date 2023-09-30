import tkinter as tk
from tkinter import filedialog, ttk
import numpy as np
import rawpy
from PIL import Image, ImageTk
import threading
import os
import queue
import concurrent.futures
import psutil
import sys
import pyexifinfo as pex

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

message_queue = queue.Queue()
stop_process_flag = False  # Initialize the stop_process_flag here

def process_single_image(file_path):
    try:
        with rawpy.imread(file_path) as raw:
            img = raw.postprocess()
        print(f"Processed Image: {file_path}")
        return img
    except Exception as e:
        message_queue.put(("status", "Error while processing the image: " + str(e)))
        message_queue.put(("done",))

def update_preview_image(img_array):
    try:
        img = Image.fromarray(np.uint8(img_array))
        img.thumbnail((600, 600))
        img_tk = ImageTk.PhotoImage(img)
        preview_image_label.config(image=img_tk)
        preview_image_label.image = img_tk
    except Exception as e:
        message_queue.put(("status", "Error while updating the preview image: " + str(e)))

def save_image(save_path, max_image):
    try:
        if max_image is None:
            message_queue.put(("status", "Error: No images were processed."))
            message_queue.put(("done",))
            return

        img_with_exif = Image.fromarray(np.uint8(max_image))
        img_with_exif.save(save_path)
        print(f"Image Saved at: {save_path}")
        message_queue.put(("status", "Maximized image saved successfully."))
    except Exception as e:
        message_queue.put(("status", "Error while saving the image: " + str(e)))

def process_images_thread(file_paths, save_path):
    global stop_process_flag
    print("Entered process_images_thread")

    if not file_paths:
        message_queue.put(("status", "No files selected."))
        message_queue.put(("done",))
        return

    if not save_path:
        message_queue.put(("status", "No save path specified."))
        message_queue.put(("done",))
        return

    total_files = len(file_paths)
    message_queue.put(("status", "Starting to process images..."))

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for index, file_path in enumerate(file_paths):
                if stop_process_flag:  # Check the stop_process_flag here
                    break
                print(f"Processing image at path: {file_path}")
                img = process_single_image(file_path)
                print(f"Image processed successfully: {file_path}")
                if index == 0:
                    max_image = img                
                else:
                    max_image = np.maximum(max_image, img)
                    if index % 5 == 0:
                        message_queue.put(("update_preview_image", max_image))
                print(f"Getting EXIF data for: {file_path}")
                data = pex.get_json(file_path)
                print(f"Got EXIF data for: {file_path}")
                try:
                    exposure_time = float(data[0]['EXIF:ExposureTime'])
                    print(f"Exposure Time for {file_path}: {exposure_time}")
                except Exception as e:
                    print(f"Error in getting Exposure Time for {file_path}: {e}")
                    print(f"EXIF data: {data}")
    except Exception as e:
        message_queue.put(("status", "Error while processing images: " + str(e)))
        message_queue.put(("done",))
        return

    if not stop_process_flag:
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
    try:
        file_paths = filedialog.askopenfilenames(title="Select .dng files", filetypes=[("DNG files", "*.dng")])
        print(f"File Paths: {file_paths}")
        save_path = filedialog.asksaveasfilename(title="Save as", defaultextension=".tiff", filetypes=[("TIFF files", "*.tiff")])
        print(f"Save Path: {save_path}")
        threading.Thread(target=process_images_thread, args=(file_paths, save_path)).start()
    except Exception as e:
        message_queue.put(("status", "Error while selecting files or save path: " + str(e)))
        message_queue.put(("done",))

def stop_process():
    global stop_process_flag
    stop_process_flag = True  # Set the stop_process_flag to True here

def restart():
    stop_button.grid_remove()
    select_files_button.grid()
    files_label.grid()
    status_label.grid_remove()
    progress_bar.grid_remove()
    details_label.grid_remove()
    preview_image_label.grid_remove()
    restart_button.grid_remove()

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
            restart_button.grid()
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

frame = ttk.Frame(app)
frame.grid()

title_label = ttk.Label(frame, text="DNG Maximizer")
title_label.grid()

files_label = ttk.Label(frame, text="Select DNG files to Maximizer:")
files_label.grid(row=1, column=0)
select_files_button = ttk.Button(frame, text="Select files", command=process_images)
select_files_button.grid(row=1, column=1)

status_var = tk.StringVar()
status_label = ttk.Label(frame, textvariable=status_var)
status_label.grid(row=2, column=0, columnspan=2)

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(frame, variable=progress_var, mode='determinate')
progress_bar.grid(row=3, column=0, columnspan=2)

details_var = tk.StringVar()
details_label = ttk.Label(frame, textvariable=details_var, wraplength=400, justify=tk.LEFT)
details_label.grid(row=4, column=0, columnspan=2)

preview_image_label = ttk.Label(frame)
preview_image_label.grid(row=5, column=0, columnspan=2)

stop_button = ttk.Button(frame, text="Stop", command=stop_process)
stop_button.grid(row=1, column=1)

restart_button = ttk.Button(frame, text="Restart", command=restart)
restart_button.grid(row=6, column=0, columnspan=2)

status_label.grid_remove()
progress_bar.grid_remove()
details_label.grid_remove()
preview_image_label.grid_remove()
stop_button.grid_remove()
restart_button.grid_remove()

app.after(100, update_ui)
app.mainloop()
