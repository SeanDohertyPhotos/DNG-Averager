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

exiftool_path = "C:\\Program Files (x86)\\exiftool\\exiftool.exe"
message_queue = queue.Queue()

def process_single_image(file_path):
    with rawpy.imread(file_path) as raw:
        img = raw.postprocess()
    return img

def process_images_thread(batch_size=10):
    def save_image(save_path, average_image):
        try:
            img_with_exif = Image.fromarray(np.uint8(average_image))
            img_with_exif.save(save_path)
            subprocess.run([exiftool_path, "-tagsFromFile", file_paths[0], "-ExposureTime=" + str(total_exposure_time), save_path])
            os.remove(save_path + "_original")
            message_queue.put(("status", "Averaged image saved successfully."))
        except Exception as e:
            message_queue.put(("status", "Error while saving the image: " + str(e)))

    file_paths = filedialog.askopenfilenames(title="Select .dng files", filetypes=[("DNG files", "*.dng")])

    if not file_paths:
        message_queue.put(("status", "No files selected."))
        return

    save_path = filedialog.asksaveasfilename(title="Save as", defaultextension=".tiff", filetypes=[("TIFF files", "*.tiff")])

    if not save_path:
        message_queue.put(("status", "No save path specified."))
        return

    total_files = len(file_paths)
    message_queue.put(("status", "Starting to process images..."))

    batch_images = []
    total_exposure_time = 0

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for index, (file_path, img) in enumerate(zip(file_paths, executor.map(process_single_image, file_paths))):
            batch_images.append(img)

            try:
                exiftool_output = subprocess.check_output([exiftool_path, "-ExposureTime", file_path])
                exposure_time = float(exiftool_output.decode("utf-8").strip().split(":")[-1].strip())
                total_exposure_time += exposure_time
            except subprocess.CalledProcessError as e:
                message_queue.put(("status", "Error while reading EXIF data: " + str(e)))
                return

            if (index + 1) % batch_size == 0 or (index + 1) == total_files:
                average_image = np.mean(batch_images, axis=0)
                save_image(save_path, average_image)
                batch_images.clear()

                message_queue.put(("status", f"Processed {index + 1}/{total_files} images"))
                message_queue.put(("progress", index + 1, total_files))

    message_queue.put(("done",))

def process_images():
    select_files_button.grid_remove()
    threading.Thread(target=process_images_thread).start()

def update_ui():
    try:
        message, *args = message_queue.get(block=False)
        if message == "status":
            status_var.set(args[0])
        elif message        == "progress":
            progress_var.set(args[0])
            progress_bar.configure(maximum=args[1])
        elif message == "done":
            select_files_button.grid()
    except queue.Empty:
        pass

    app.after(100, update_ui)

app = tk.Tk()
app.title("DNG Averager")

frame = ttk.Frame(app, padding="10 10 10 10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ttk.Label(frame, text="Select DNG files to average:").grid(row=0, column=0, sticky=tk.W)
select_files_button = ttk.Button(frame, text="Select files", command=process_images)
select_files_button.grid(row=0, column=1, sticky=tk.E)

status_var = tk.StringVar()
status_label = ttk.Label(frame, textvariable=status_var)
status_label.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(frame, variable=progress_var, mode='determinate')
progress_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

app.after(100, update_ui)
app.mainloop()

