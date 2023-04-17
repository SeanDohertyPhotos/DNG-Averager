# DNG Averager

DNG Averager is a simple Python-based graphical application that helps photographers average a series of DNG images to combine exposures into a longer exposure, reduce noise and improve image quality. The program provides real-time progress feedback, a preview image during processing, and the ability to stop the process at any time.

## Features

- User-friendly graphical interface
- Support for large numbers multiple DNG image files
- Optomized for multithreaded CPU's and utlizes a batching method.
- Real-time progress updates
- Preview image during processing
- Option to stop the process at any time
- Finished message and sound notification upon completion

## Requirements

- Python 3.6 or later
- tkinter
- numpy
- rawpy
- PIL (Pillow)
- threading
- subprocess
- concurrent.futures
- psutil

## Installation

1. Ensure Python 3.6 or later is installed on your system.

2. Install the required Python packages using pip: `pip install numpy rawpy Pillow psutil`

3. Download and install [ExifTool](https://exiftool.org/) if not already installed. Make sure to add the ExifTool executable to your system's PATH variable or modify the `exiftool_path` variable in the program.

4. Download the DNG Averager Python script from this repository.

## Usage

1. Run the DNG Averager script: `python dng_averager.py`

2. Click on the "Select files" button to choose the DNG files you want to average.

3. After selecting the files, choose a location to save the output TIFF file.

4. The program will start processing the images and display real-time progress updates and a preview image.

5. If needed, you can click on the "Stop" button to cancel the process.

6. Once the process is complete, a "Finished!" message will be displayed, and a beep sound will be played.

## Contributing

If you'd like to contribute to the DNG Averager project, feel free to fork the repository, make changes, and submit pull requests. Any feedback and suggestions are also welcome.

## License

DNG Averager is released under the MIT License. For more information, see the [LICENSE](LICENSE) file.
