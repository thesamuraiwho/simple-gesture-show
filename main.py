# Author: Brandon Le
# Purpose: Simple desktop app to create a gesture gallery from a folder of images
# Modified from https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Img_Viewer.py
# Modified from https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Desktop_Widget_Timer.py

# Inspired by AdorkaStock and Line-of-Action

import PySimpleGUI as sg
import os
from PIL import Image, ImageTk, ImageOps
import io
import random
import time
from enum import Enum

# TODO Bug: Fix timer element when selecting new images should reset rather than continue?

# TODO Feat: List thumbnails instead of file names
# TODO Feat: Recursive file directory access
# TODO Feat: Add controls for basic image maniuplation like flipping and grayscale
# TODO Feat: Thumbnails in temporary directory and delete this directory when program exits
#   to avoid redoing image processing work

# Constants
SEC = 100 # 1 sec
MIN = 6000 # 1 min
IMG_TYPES = (".png", ".jpg", ".jpeg", ".tiff", ".bmp") # PIL supported image types
MODES_KEYS = ["-CONST_MODE-", "-CLASS_MODE-"]
MODES_VALUES = ["-LAYOUT_CONST-", "-LAYOUT_CLASS-"]

CONST_KEYS = ['-CONST_30SEC-', '-CONST_1MIN-', '-CONST_2MIN-', '-CONST_5MIN-', 
    '-CONST_10MIN-', '-CONST_15MIN-', '-CONST_30MIN-', '-CONST_60MIN-']
CONST_VALUES = [int(0.5 * MIN), MIN, 2 * MIN, 5 * MIN, 10 * MIN, 15 * MIN, 30 * MIN, 60 * MIN]

CLASS_KEYS = ['-CLASS_DEFAULT-', '-CLASS_RAPID-', '-CLASS_LEISURE-']
# test_class = [[[1, 2 * SEC], [2, 3 * SEC], [3, 4 * SEC]],
#     [[4, 5 * SEC], [5, 7 * SEC], [6, 10 * SEC]], 
#     [[3, 3 * SEC], [4, 4 * SEC], [5, 5 * SEC]]]
CLASS_DEFAULT = [[10, int(0.5 * MIN)], [5, MIN], [2, 5 * MIN], [1, 10 * MIN]]
CLASS_RAPID = [[4, int(0.25 * MIN)], [4, int(0.5 * MIN)], [2, MIN], [2, 5 * MIN]]
CLASS_LEISURE = [[10, MIN], [4, 5 * MIN], [2, 15 * MIN], [1, 30 * MIN]]

class Mode(Enum):
    CONSTANT = 0
    CLASS = 1

class Clock():
    def __init__(self):
        self.next_timeout = 3000 #1000 # 100 = 1 seconds
        self.current_time = 0
        self.time_diff = self.next_timeout
        self.paused = True
        self.end_time = 0

    def update_clock(self, new_timeout):
        self.next_timeout = new_timeout
        self.current_time = time_as_int()
        self.end_time = self.current_time + self.next_timeout
        self.time_diff = self.next_timeout
    
    def reset_clock(self):
        self.current_time = time_as_int()
        self.end_time = self.current_time + self.next_timeout
        self.time_diff = self.next_timeout

    def pause(self):
        self.paused = not self.paused
        if self.paused:
            self.time_diff = self.end_time - self.current_time
        else:
            self.current_time = time_as_int()
            self.end_time = self.current_time + self.time_diff
    
    def decrement(self):
        self.current_time = time_as_int()
        self.time_diff = self.end_time - self.current_time

class Class_Mode():
    def __init__(self, class_list=CLASS_DEFAULT, class_mode_str='Default', 
        class_index=0, class_poses=[0, CLASS_DEFAULT[0][1]]):
        self.class_list = class_list
        self.class_mode_str = class_mode_str
        self.class_index = class_index
        self.class_poses = class_poses
    
    def set_class_mode(self, class_list, class_mode_str, class_index, class_poses):
        self.class_list = class_list
        self.class_mode_str = class_mode_str
        self.class_index = class_index
        self.class_poses = class_poses
    
    def set_choice(self, class_list, class_mode_str):
        self.class_list = class_list
        self.class_mode_str = class_mode_str
        self.class_index = 0
        self.class_poses = [0, class_list[0][1]]

    def get_poses(self):
        return self.class_list[self.class_index][0]
    
    def get_pose(self):
        return self.class_poses[0]
    
    def get_timeout(self):
        return self.class_list[self.class_index][1]

    def increment(self):
        # If we complete a class mode session, reset to the beginning
        length = len(self.class_list) - 1
        max_poses = self.class_list[self.class_index][0] - 1
        if self.class_index == length and self.class_poses[0] == max_poses:
            self.class_index = 0
            self.class_poses = [0, self.class_list[0][1]]
        # If we complete all the poses but not the class mode session, increment the class index
        # and reset the class poses counter and set the timeout to the new class index
        elif self.class_index < length and self.class_poses[0] == max_poses:
            self.class_index += 1
            self.class_poses = [0, self.class_list[self.class_index][1]]
        else:
            self.class_poses[0] += 1

    def display(self):
        return f'Selection: {self.class_mode_str}\nClass index: {self.class_index + 1} ' \
            + f'Poses: {self.get_poses()} Current pose: {self.get_pose() + 1}\n' \
            + f'Time: {time_as_string(self.get_timeout())}\n' \
            + self.display_class_list()

    def display_class_list(self):
        cl ="\nMode Poses\n"
        for i in range(len(self.class_list)):
	        cl += f"Poses: {self.class_list[i][0]} Timeout: {time_as_string(self.class_list[i][1])}\n"
        return cl

def Radio(key, text, group_id, default=False): 
    return sg.Radio(key=key, text=text, group_id=group_id, default=default, enable_events=True)

def Button(key, text, color="#1f6650", font=('Arial', 12), disabled=False): 
    return sg.Button(key=key, button_text=text, button_color=color, size=(8, 2), font=font, disabled=disabled)

def time_as_int():
    return int(round(time.time() * 100))

def time_as_string(time):
    if time < 0:
        time = 0
    return '{:02d}:{:02d}'.format(((time) // 100) // 60, ((time) // 100) % 60)

def get_img_data(f, maxsize=(1600, 950), first=False):#(1200, 850), first=False):
    """Generate image data using PIL
    """

    img = Image.open(f)
    img_size = img.size
    img_width, img_height = img_size
    # if the original width is larger than the max width
    if img_width > maxsize[0]:
        scale_factor_width = maxsize[0] / img_width

        # if the original height is larger than the max height after scaling by the width,
        #   scale the image to this scale factor instead
        if (img_height * scale_factor_width) > maxsize[1]:
            scale_factor_height = maxsize[1] / img_height
            img.thumbnail((img_width * scale_factor_height, img_height * scale_factor_height))
        # else if the original height is less than the max height after scaling,
        #   scale by just the width
        else:
            img.thumbnail((img_width * scale_factor_width, img_height * scale_factor_width))
    # else if the original width is smaller
    else:
        # if the original height is larger, scale by just the height
        if img_height > maxsize[1]:
            scale_factor_height = maxsize[1] / img_height
            img.thumbnail((img_width * scale_factor_height, img_height * scale_factor_height))
        # else the original width and height are smaller so enlarge them by the smallest scale factor
        else:
            scale_factor_width = maxsize[0] / img_width
            scale_factor_height = maxsize[1] / img_height
            scale_factor = min(scale_factor_width, scale_factor_height)
            img.thumbnail((img_width * scale_factor, img_height* scale_factor))

    if first:                     # tkinter is inactive the first time
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()
    return ImageTk.PhotoImage(img)

def grayscale(f):
    bw_img = ImageOps.grayscale(f)
    bw_img.show()
    return bw_img

def check_const_choice(values, clock):
    for choice in range(len(CONST_KEYS)):
        if values[CONST_KEYS[choice]]:
            clock.update_clock(CONST_VALUES[choice])
            break
    return clock

def check_class_choice(event, values, class_settings, clock):
    if values[event] and event == '-CLASS_DEFAULT-' :
        class_settings.set_choice(CLASS_DEFAULT, 'Default')
    elif values[event] and event == '-CLASS_RAPID-':
        class_settings.set_choice(CLASS_RAPID, 'Rapid')
    elif values[event] and event == '-CLASS_LEISURE-':
        class_settings.set_choice(CLASS_LEISURE, 'Leisure')
    clock.update_clock(class_settings.class_poses[1])    
    return class_settings, clock

def main():
    sg.theme('lightgreen6')
    settings = sg.UserSettings()
    clock = Clock()
    class_settings = Class_Mode()
    mode = Mode.CONSTANT
    filename = folder = ""
    fnames = []
    num_files = img = 0
    file_num_display_elem = sg.Text(key='-FILE_NUM-', text='', size=(15,1))
    image_elem = sg.Image(key='-IMAGE_ELEM-', data=None)
    col = [[image_elem]]
    settings_load = False
    
    folder_browser = [[sg.FolderBrowse(button_text="Browse", 
        initial_folder=settings['-FOLDER-'] if settings['-FOLDER-'] else os.getcwd(),
        enable_events=True, font=('Helvetica', 16), key="-FOLDER_BROWSER-")]]

    files = [[sg.Listbox(key='-LISTBOX-', values=fnames, change_submits=True, size=(40, 10))],
        [Button('-PREV-', '⏪', disabled=True), Button('-NEXT-', '⏩', disabled=True),
            file_num_display_elem]]

    session = [[sg.Text('Session Type')], [sg.HSeparator()],
        [Radio('-CONST_MODE-', 'Constant Mode', 1, default=True)], 
        [Radio('-CLASS_MODE-', 'Class Mode', 1)]]

    const_mode = [[sg.Text('Constant Mode Options')], [sg.HSeparator()],
        [Radio('-CONST_30SEC-', '30 sec', 2, default=True), Radio('-CONST_1MIN-', '1 min', 2),
            Radio('-CONST_2MIN-', '2 min', 2), Radio('-CONST_5MIN-', '5 min', 2)],
        [Radio('-CONST_10MIN-', '10 min', 2), Radio('-CONST_15MIN-', '15 min', 2),
            Radio('-CONST_30MIN-', '30 min', 2), Radio('-CONST_60MIN-', '60 min', 2)]]

    class_mode = [[sg.Text('Class Mode Options')], [sg.HSeparator()],
        [Radio('-CLASS_DEFAULT-', 'Default', 3, default=True), 
            Radio('-CLASS_RAPID-', 'Rapid', 3),
            Radio('-CLASS_LEISURE-', 'Leisure', 3)],
            [sg.Text(key='-CLASS_SELECTION-', text=class_settings.display())]]

    timer = [[sg.Text(key='-TIMER-', text='00:30', size=(4, 1), 
            font=('Helvetica', 32), justification='center')]]
    
    controls =[[Button('-RUN_PAUSE-', '▶️', color=('white', '#001480'), disabled=True),
        Button('-RESET-', 'RESET', color=('white', '#007339')),
        Button('-EXIT-', 'EXIT', color=('white', '#8b1a1a'))]]

    layout_const = [[sg.Column(const_mode, key="-LAYOUT_CONST-")]]
    layout_class = [[sg.Column(class_mode, key="-LAYOUT_CLASS-", visible=False)]]
    layout = [[sg.Column(key='-CONTROLS-', vertical_alignment='top', layout=folder_browser 
        + session + layout_const + layout_class + timer + files + controls), 
        sg.Column(key='-IMAGE-', vertical_alignment='top', layout=col, visible=False)]]
    window = sg.Window('Simple Gesture Show', layout, return_keyboard_events=True,
        location=(0, 0), size=(1920, 1080), background_color='#272927',
        resizable=True, use_default_focus=False, icon='icon.ico').Finalize()
    window.Maximize()

    while True:
        event, values = window.read(timeout=10)#10000)#100)#15)
        if event in (sg.WIN_CLOSED, '-EXIT-'):
            break

        elif event == '-FOLDER_BROWSER-':
            folder = values['-FOLDER_BROWSER-'] # Get the folder containing the images from the user
            if folder:
                flist0 = os.listdir(folder) # get list of files in folder

                # create sub list of image files (no sub folders, no wrong file types)
                fnames = [f for f in flist0 if os.path.isfile(
                    os.path.join(folder, f)) and f.lower().endswith(IMG_TYPES)]

                random.shuffle(fnames) # Randomly shuffle the order of files
                num_files = len(fnames)  # number of images found
                if num_files != 0:
                    del flist0  # file list object deleted since it is no longer needed
                    filename = os.path.join(folder, fnames[0])  # initialize to the first file in the list
                    window['-IMAGE-'].update(visible=True)
                    window['-LISTBOX-'].update(values=fnames)
                    window['-FILE_NUM-'].update(f'File 1 of {num_files}')
                    window['-IMAGE_ELEM-'].update(data=get_img_data(filename, first=True))
                    settings['-FOLDER-'] = folder
                    clock.reset_clock()
                else:
                    sg.popup('No images in folder')
        
        elif event == '-RESET-':
            clock.reset_clock()

        elif event in ('-NEXT-', '-PREV-'):
            if event == '-NEXT-':
                img += 1
                if img >= num_files:
                    img -= num_files
            elif event == '-PREV-':
                img -= 1
                if img < 0:
                    img += num_files
            filename = os.path.join(folder, fnames[img])
            clock.reset_clock()

        elif event == '-LISTBOX-':            
            f = values['-LISTBOX-'][0]        
            filename = os.path.join(folder, f)
            img = fnames.index(f)             
            clock.reset_clock()

        elif event in MODES_KEYS:
            for choice in range(len(MODES_KEYS)):
                if values[MODES_KEYS[choice]]:
                    mode = Mode(choice)
                    new_layout = MODES_VALUES[choice]
                    for lay in MODES_VALUES:
                        window[lay].update(visible=False)
                    window[new_layout].update(visible=True)
                    clock.paused = True
                    clock.reset_clock()
                    window['-RUN_PAUSE-'].update('▶️')
                    break

            if mode == Mode.CONSTANT:
                clock = check_const_choice(values, clock)
            else:
                class_settings, clock = check_class_choice(event, values, class_settings, clock)
                window['-CLASS_SELECTION-'].update(class_settings.display())

        elif event in CONST_KEYS:
            clock = check_const_choice(values, clock)

        elif event in CLASS_KEYS:
            class_settings, clock = check_class_choice(event, values, class_settings, clock)
            window['-CLASS_SELECTION-'].update(class_settings.display())

        if settings['-FOLDER-'] and not settings_load:
            folder = settings['-FOLDER-']
            flist0 = os.listdir(folder) # get list of files in folder

            # create sub list of image files (no sub folders, no wrong file types)
            fnames = [f for f in flist0 if os.path.isfile(
                os.path.join(folder, f)) and f.lower().endswith(IMG_TYPES)]

            random.shuffle(fnames) # Randomly shuffle the order of files
            num_files = len(fnames)  # number of images found
            if num_files != 0:
                del flist0  # file list object deleted since it is no longer needed
                filename = os.path.join(folder, fnames[0])  # initialize to the first file in the list
                window['-IMAGE-'].update(visible=True)
                window['-LISTBOX-'].update(values=fnames)
                window['-FILE_NUM-'].update(f'File 1 of {num_files}')
                window['-IMAGE_ELEM-'].update(data=get_img_data(filename, first=True))
                settings['-FOLDER-'] = folder
                settings_load = True
            else:
                sg.popup('No images in folder')

        if folder and filename:
            window['-PREV-'].update(disabled=False)
            window['-NEXT-'].update(disabled=False)
            window['-RUN_PAUSE-'].update(disabled=False)
            if event == '-RUN_PAUSE-':
                clock.pause()
                window['-RUN_PAUSE-'].update('▶️' if clock.paused else '⏸️')

            # update window with new image
            image_elem.update(data=get_img_data(filename, first=True))
            window['-IMAGE_ELEM-'].update(data=get_img_data(filename, first=True))
            # update page display
            file_num_display_elem.update(f'File {img+1} of {num_files}')
            window.Refresh()

        if clock.time_diff <= 0 and not clock.paused:
            if mode == Mode.CLASS:
                class_settings.increment()
                clock.next_timeout = class_settings.class_poses[1]
                window['-CLASS_SELECTION-'].update(class_settings.display())
            clock.reset_clock()
            img += 1
            if img >= num_files:
                img %= num_files
            filename = os.path.join(folder, fnames[img])

        elif clock.time_diff > 0 and not clock.paused:
            clock.decrement()

        window['-TIMER-'].update(time_as_string(clock.time_diff))
    window.close()

if __name__ == "__main__":
    main()
