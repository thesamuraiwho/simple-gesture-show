# Author: Brandon Le
# Purpose: Simple desktop app to create a gesture gallery from a folder of images
# Modified from https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Img_Viewer.py
# Modified from https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Desktop_Widget_Timer.py

# Inspired by AdorkaStock and Line-of-Action

import PySimpleGUI as sg
import os
from PIL import Image, ImageTk
import io
import random
import time
from enum import Enum

# TODO Bug: Fix timer element when selecting new images should reset rather than continue?

# TODO Feat: List thumbnails instead of file names
# TODO Feat: Recursive file directory access
# TODO Feat: Set increments via a input box
# TODO Feat: Add controls for basic image maniuplation like flipping and grayscale
# TODO Feat: Aave thumbnails in temporary directory and delete this directory when program exits
#   to avoid redoing image processing work

# Constants
SEC = 100 # 1000ms == 1 sec
MIN = 6000 # 60000ms == 1 min
MODES_KEYS = ["-SESSION_CONST_MODE-", "-SESSION_CLASS_MODE-"]
MODES_VALUES = ["-LAYOUT_CONST-", "-LAYOUT_CLASS-"]

CONST_KEYS = ['-CONST_30SEC-', '-CONST_1MIN-', '-CONST_2MIN-', '-CONST_5MIN-', 
    '-CONST_10MIN-', '-CONST_15MIN-', '-CONST_30MIN-', '-CONST_60MIN-']
CONST_VALUES = [int(0.5 * MIN), MIN, 2 * MIN, 5 * MIN, 10 * MIN, 15 * MIN, 30 * MIN, 60 * MIN]

CLASS_KEYS = ['-CLASS_DEFAULT-', '-CLASS_RAPID-', '-CLASS_LEISURE-']
test_class = [[[2, 2 * SEC], [3, 3 * SEC], [4, 4 * SEC]],
    [[4, 5 * SEC], [5, 7 * SEC], [6, 10 * SEC]], 
    [[3, 3 * SEC], [4, 4 * SEC], [5, 5 * SEC]]]
CLASS_DEFAULT = test_class[0]#[[10, int(0.5 * MIN)], [5, MIN], [2, 5 * MIN], [1, 10 * MIN]]
CLASS_RAPID = test_class[1]#[[4, int(0.25 * MIN)], [4, int(0.5 * MIN)], [2, MIN], [2, 5 * MIN]]
CLASS_LEISURE = test_class[2]#[[10, MIN], [4, 5 * MIN], [2, 15 * MIN], [1, 30 * MIN]]

class Session_Mode(Enum):
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

    def update_paused(self):
        self.paused = not self.paused
    
    def decrement(self):
        self.current_time = time_as_int()
        self.time_diff = self.end_time - self.current_time

class Class_Mode():

    # def __init__(self):
    #     self.class_list = CLASS_DEFAULT
    #     self.class_mode_str = 'Default'
    #     self.class_index = 0
    #     self.class_poses = [0, class_list[0][1]]

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
        if self.class_index >= len(self.class_list):
            self.class_index = 0
            self.class_poses = [0, class_list[0][1]]
        
        # If we complete all the poses but not the class mode session, increment the class index
        # and reset the class poses counter and set the timeout to the new class index
        elif self.class_index < len(self.class_list) and self.class_poses[0] == self.class_list[self.class_index][0]:
            self.class_index += 1
            self.class_poses = [0, self.class_list[self.class_index][1]]
        else:
            self.class_poses[0] += 1

def Radio(key, text, group_id, default=False): return sg.Radio(key=key, text=text, group_id=group_id, 
    default=default, enable_events=True)

def Button(key, text, color="#1f6650", disabled=False): return sg.Button(key=key, button_text=text, 
    button_color=color, size=(8, 2), font=('Helvetica', 12), disabled=disabled)

def time_as_int():
    return int(round(time.time() * 100))

def time_as_string(time):
    return '{:02d}:{:02d}'.format(((time) // 100) // 60, ((time) // 100) % 60)

def get_img_data(f, maxsize=(1200, 850), first=False):
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

    # img.thumbnail(maxsize)
    if first:                     # tkinter is inactive the first time
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()
    return ImageTk.PhotoImage(img)

def check_const_choice(values):
    for choice in range(len(CONST_KEYS)):
        if values[CONST_KEYS[choice]]:
            next_timeout = CONST_VALUES[choice]
            current_time = time_as_int()
            end_time = current_time + next_timeout
            time_diff = next_timeout
            break
    return next_timeout, current_time, end_time, time_diff

def check_class_choice(event, values, window, class_settings, clock):
    if values[event] and event == '-CLASS_DEFAULT-' :
        class_settings.set_choice(CLASS_DEFAULT, 'Default')
    elif values[event] and event == '-CLASS_RAPID-':
        class_settings.set_choice(CLASS_RAPID, 'Rapid')
    elif values[event] and event == '-CLASS_LEISURE-':
        class_settings.set_choice(CLASS_LEISURE, 'Leisure')
    clock.update_clock(class_settings.class_poses[1])
    window['-CLASS_SELECTION-'].update(f'Selection: {class_settings.class_mode_str}'
        f'\nClass index: {class_settings.class_index}\nPoses: {class_settings.get_poses()}'
        f'\nCurrent pose: {class_settings.get_pose()}\nTime: {time_as_string(class_settings.get_timeout())}')
    
    return class_settings, clock

def main():
    sg.theme('lightgreen6')
    session_mode = Session_Mode.CONSTANT
    folder = ""
    fnames = []
    file_num_display_elem = sg.Text(key='-FILE_NUM-', text='', size=(15,1))
    image_elem = sg.Image(key='-IMAGE_ELEM-', data=None)
    col = [[image_elem]]
    img = 0
    num_files = 0
    clock = Clock()
    class_settings = Class_Mode()
    
    folder_browser = [[sg.FolderBrowse(button_text="Browse", initial_folder=os.getcwd(),
        enable_events=True, font=('Helvetica', 16), key="-FOLDER_BROWSER-")]]

    files = [[sg.Listbox(key='-LISTBOX-', values=fnames, change_submits=True, size=(40, 10))],
        [Button('-PREV-', 'Prev', color="#1f6650"), Button('-NEXT-', 'Next', color="#1f6650"), 
            file_num_display_elem]]

    # Get session settings
    session = [[sg.Text('Session Type')], [sg.HSeparator()],
        [Radio('-SESSION_CONST_MODE-', 'Constant Mode', 1, default=True)], 
        [Radio('-SESSION_CLASS_MODE-', 'Class Mode', 1)]]

    const_mode = [[sg.Text('Constant Mode Options')], [sg.HSeparator()],
        [Radio('-CONST_30SEC-', '30 sec', 2, default=True), Radio('-CONST_1MIN-', '1 min', 2),
            Radio('-CONST_2MIN-', '2 min', 2), Radio('-CONST_5MIN-', '5 min', 2)],
        [Radio('-CONST_10MIN-', '10 min', 2), Radio('-CONST_15MIN-', '15 min', 2),
            Radio('-CONST_30MIN-', '30 min', 2), Radio('-CONST_60MIN-', '60 min', 2)]]

    class_mode = [[sg.Text('Class Mode Options')], [sg.HSeparator()],
        [Radio('-CLASS_DEFAULT-', 'Default', 3, default=True), 
            Radio('-CLASS_RAPID-', 'Rapid', 3),
            Radio('-CLASS_LEISURE-', 'Leisure', 3)],
            [sg.Text(key='-CLASS_SELECTION-', text= f'Selection: {class_settings.class_mode_str}\nClass index: {class_settings.class_index}' 
                + f'\nPoses: {class_settings.get_poses()}\nCurrent pose: {class_settings.get_pose()}'
                + f'\nTime: {time_as_string(class_settings.get_timeout())}')]]
                
    timer_layout = [[sg.Text(key='-TIMER-', text='00:30', size=(4, 1), font=('Helvetica', 32), justification='center')],
        [Button('-RUN_PAUSE-', 'Run', color=('white', '#001480'), disabled=True),
            Button('-RESET-', 'Reset', color=('white', '#007339')),
            Button('-EXIT-', 'Exit', color=('white', '#8b1a1a'))]]

    layout_const = [[sg.Column(const_mode, key="-LAYOUT_CONST-")]]
    layout_class = [[sg.Column(class_mode, key="-LAYOUT_CLASS-", visible=False)]]
    layout = [[sg.Column(key='-CONTROLS-', vertical_alignment='top', layout=folder_browser + files 
        + session + layout_const + layout_class + timer_layout), 
        sg.Column(key='-IMAGE-', vertical_alignment='top', layout=col, visible=False)]]
    window = sg.Window('Simple Gesture Show', layout, return_keyboard_events=True,
                       location=(0, 0), size=(1920, 1080), background_color='#272927',
                       resizable=True, use_default_focus=False)

    while True:
        event, values = window.read(timeout=100)#10000)#100)#15)
        print(f"event: {event}\nvalues: {values}\nsession mode: {session_mode}\ntime diff: {time_as_string(clock.time_diff)}\n\n")

        if event in (sg.WIN_CLOSED, '-EXIT-'):
            break

        elif event == '-FOLDER_BROWSER-':
            folder = values['-FOLDER_BROWSER-'] # Get the folder containing the images from the user
            if not folder:
                # TODO Should gracefully allow re-browsing
                sg.popup_cancel('Cancelling')
                raise SystemExit()

            img_types = (".png", ".jpg", ".jpeg", ".tiff", ".bmp") # PIL supported image types
            flist0 = os.listdir(folder) # get list of files in folder

            # create sub list of image files (no sub folders, no wrong file types)
            fnames = [f for f in flist0 if os.path.isfile(
                os.path.join(folder, f)) and f.lower().endswith(img_types)]

            random.shuffle(fnames) # Randomly shuffle the order of files
            num_files = len(fnames)  # number of images found
            if num_files == 0:
                # TODO Should gracefully allow re-browsing
                sg.popup('No files in folder')
                raise SystemExit()

            del flist0  # file list object deleted since it is no longer needed
            filename = os.path.join(folder, fnames[0])  # initialize to the first file in the list

            print(f"folder: {folder}\nfnames:{fnames}\nnum_files: {num_files}")
            window['-IMAGE-'].update(visible=True)
            window['-LISTBOX-'].update(values=fnames)
            window['-FILE_NUM-'].update(f'File 1 of {num_files}')
            window['-IMAGE_ELEM-'].update(data=get_img_data(filename, first=True))
        
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
                    session_mode = Session_Mode(choice)
                    print(f"Session_Mode(choice): {Session_Mode(choice)}\nsession_mode: {session_mode}\n")
                    new_layout = MODES_VALUES[choice]
                    for lay in MODES_VALUES:
                        window[lay].update(visible=False)
                    window[new_layout].update(visible=True)
                    break

            if session_mode == Session_Mode.CONSTANT:
                next_timeout, current_time, end_time, time_diff = check_const_choice(values)

            else:
                class_settings, clock = check_class_choice(event, values, window, class_settings, clock)

        elif event in CONST_KEYS:
            next_timeout, current_time, end_time, time_diff = check_const_choice(values)

        elif event in CLASS_KEYS:
            print(f"\n\nvalues[event]: {values[event]}\n\n")
            class_settings, clock = check_class_choice(event, values, window, class_settings, clock)

        if folder:
            window['-RUN_PAUSE-'].update(disabled=False)
            if event == '-RUN_PAUSE-':
                clock.update_paused()
                if clock.paused:
                    clock.time_diff = clock.end_time - clock.current_time
                else:
                    clock.current_time = time_as_int()
                    clock.end_time = clock.current_time + clock.time_diff
                window['-RUN_PAUSE-'].update('Run' if clock.paused else 'Pause')

            # update window with new image
            image_elem.update(data=get_img_data(filename, first=True))
            window['-IMAGE_ELEM-'].update(data=get_img_data(filename, first=True))
            # update page display
            file_num_display_elem.update(f'File {img+1} of {num_files}')
            window.Refresh()

        if clock.time_diff <= 0 and not clock.paused:
            print("\nRESET\n")
            if session_mode == Session_Mode.CLASS:
                print("\n\nClass mode reset\n\n")
                class_settings.increment()
                clock.next_timeout = class_settings.class_poses[1]
                window['-CLASS_SELECTION-'].update(f'Selection: {class_settings.class_mode_str}'
                    f'\nClass index: {class_settings.class_index}\nPoses: {class_settings.get_poses()}'
                    f'\nCurrent pose: {class_settings.get_pose()}\nTime: {time_as_string(class_settings.get_timeout())}')
            clock.reset_clock()
            img += 1
            if img >= num_files:
                img %= num_files
            filename = os.path.join(folder, fnames[img])

        elif clock.time_diff > 0 and not clock.paused:
            print("\nTIMER RUNNING\n")
            clock.decrement()

        window['-TIMER-'].update(time_as_string(clock.time_diff))
    window.close()

if __name__ == "__main__":
    main()
