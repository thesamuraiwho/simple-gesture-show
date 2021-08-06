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
SEC = 1000 # 1000ms == 1 sec
MIN = 60000 # 60000ms == 1 min
MODES_KEYS = ["-SESSION_CONST_MODE-", "-SESSION_CLASS_MODE-", "-SESSION_CUSTM_MODE-"]
MODES_VALUES = ["-LAYOUT_CONST-", "-LAYOUT_CLASS-", "-LAYOUT_CUSTM-"]

class Session_Mode(Enum):
    CONSTANT = 0
    CLASS = 1
    CUSTOM = 2

def Radio(key, text, group_id, default=False): return sg.Radio(key=key, text=text, group_id=group_id, 
    default=default, enable_events=True)

def time_as_int():
    return int(round(time.time() * 100))

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


def main():
    sg.theme('lightgreen6')
    session_mode = Session_Mode.CONSTANT
    next_timeout = 1000 # 100 = 1 seconds
    current_time, time_diff, paused = 0, next_timeout, True
    start_time = time_as_int()
    end_time = 0
    folder = ""
    fnames = []
    file_num_display_elem = sg.Text(key='-FILE_NUM-', text='', size=(15,1))
    image_elem = sg.Image(key='-IMAGE_ELEM-', data=None)
    col = [[image_elem]]
    num_files = 0
    

    folder_browser = [[sg.FolderBrowse(button_text="Browse",
        initial_folder=os.getcwd(),
        enable_events=True,
        font=('Helvetica', 20),
        key="-FOLDER_BROWSER-")]]

    files = [[sg.Listbox(key='-LISTBOX-', values=fnames, change_submits=True, size=(50, 10))],
        [sg.Button(key='-PREV-', button_text='Prev', size=(8, 2)), 
            sg.Button(key='-NEXT-', button_text='Next', size=(8, 2)), file_num_display_elem]]

    # Get session settings
    session = [[sg.Text('Session Type')], [sg.HSeparator()],
        [Radio('-SESSION_CONST_MODE-', 'Constant Length', 1, default=True), 
            Radio('-SESSION_CLASS_MODE-', 'Class Mode', 1),
            Radio('-SESSION_CUSTM_MODE-', 'Custom Mode', 1)]]

    const_mode = [[sg.Text('Constant Mode Options')], [sg.HSeparator()],
        [Radio('-CONST_30SEC-', '30 secs', 2, default=True), 
            Radio('-CONST_1MIN-', '1 min', 2),
            Radio('-CONST_2MIN-', '2 min', 2),
            Radio('-CONST_5MIN-', '5 min', 2)],
        [Radio('-CONST_10MIN-', '10 min', 2),
            Radio('-CONST_15MIN-', '15 min', 2),
            Radio('-CONST_30MIN-', '30 min', 2),
            Radio('-CONST_60MIN-', '60 min', 2)]]

    class_mode = [[sg.Text('Class Mode Options')], [sg.HSeparator()],
        [Radio('-CLASS_DEFAULT-', 'Default', 3, default=True), 
            Radio('-CLASS_RAPID-', 'Rapid', 3),
            Radio('-CLASS_LEISURE', 'Leisure', 3)]]

    custm_mode = [[sg.Text('Custom Mode Timer Adjustment')], [sg.HSeparator()],
        [sg.Text(key='-CUR-TIMEOUT-', text='Current timeout: 1 Minute'), 
            sg.Input(key='-TIMER-VALUE-', default_text=1, size=(8, 2)), 
            sg.Radio(key='-MIN-', text='Minutes', group_id=4, enable_events=True, default=True),
            sg.Radio(key='-SEC-', text='Seconds', group_id=4, enable_events=True)],
        [sg.Button(key='-DEC-TIMER-', button_text='-', button_color=('white', '#00F'), size=(8, 2)),
            sg.Button(key='-INC-TIMER-', button_text='+', button_color=('white', '#FFA500'), size=(8, 2))]]
                
    timer_layout = [[sg.Text(key='-TIMER-', text='00:00', size=(4, 1), font=('Helvetica', 32), justification='center')],
        [sg.Button(key='-RUN-PAUSE-', button_text='Run', button_color=('white', '#001480'), size=(8, 2)),
            sg.Button(key='-RESET-', button_text='Reset', button_color=('white', '#007339'), size=(8, 2)),
            sg.Exit(key='-EXIT-', button_text='Exit', button_color=('white', 'firebrick4'), size=(8, 2))]]

    layout_const = [[sg.Column(const_mode, key="-LAYOUT_CONST-")]]
    layout_class = [[sg.Column(class_mode, key="-LAYOUT_CLASS-", visible=False)]]
    layout_custm = [[sg.Column(custm_mode, key="-LAYOUT_CUSTM-", visible=False)]]
    layout = [[folder_browser], [sg.Column(key='-CONTROLS-', vertical_alignment='top', layout=files + session 
        + layout_const + layout_class + layout_custm + timer_layout), 
        sg.Column(key='-IMAGE-', vertical_alignment='top', layout=col, visible=False)]]

    # loop reading the user input and displaying image, filename
    img = 0

    window = sg.Window('Simple Gesture Show', layout, return_keyboard_events=True,
                       location=(0, 0), size=(1920, 1080), background_color='#272927',
                       resizable=True, use_default_focus=False)

    while True:
        # print(sg.Window.get_screen_size())
        # print(paused)
        event, values = window.read(timeout=15)
        print(f"event: {event}\nvalues: {values}\n")

        if event in (sg.WIN_CLOSED, '-EXIT-'):
            break

        if event == '-FOLDER_BROWSER-':
            # Get the folder containing the images from the user
            folder = values['-FOLDER_BROWSER-']
            if not folder:
                # TODO Should gracefully allow re-browsing
                sg.popup_cancel('Cancelling')
                raise SystemExit()

            # PIL supported image types
            img_types = (".png", ".jpg", ".jpeg", ".tiff", ".bmp")

            # get list of files in folder
            flist0 = os.listdir(folder)

            # create sub list of image files (no sub folders, no wrong file types)
            fnames = [f for f in flist0 if os.path.isfile(
                os.path.join(folder, f)) and f.lower().endswith(img_types)]

            # Randomly shuffle the order of files
            random.shuffle(fnames)

            num_files = len(fnames)  # number of images found
            if num_files == 0:
                # TODO Should gracefully allow re-browsing
                sg.popup('No files in folder')
                raise SystemExit()

            del flist0  # no longer needed

            # make these 2 elements outside the layout as we want to "update" them later
            # initialize to the first file in the list
            filename = os.path.join(folder, fnames[0])  # name of first file in list
            # image_elem = sg.Image(data=get_img_data(filename, first=True))
            # filename_display_elem = sg.Text(filename, size=(50, 3))#(80, 3))
            # file_num_display_elem = sg.Text('File 1 of {}'.format(num_files), size=(15, 1))

            # define layout, show and read the form
            # col = [[filename_display_elem],
            #        [image_elem]]
            # col = [[image_elem]]

            print(f"folder: {folder}\nfnames:{fnames}\nnum_files: {num_files}")

            # files = [[sg.Listbox(key='-LISTBOX-', values=fnames, change_submits=True, size=(50, 30))],
            #     [sg.Button(key='-PREV-', button_text='Prev', size=(8, 2)), 
            #     sg.Button(key='-NEXT-', button_text='Next', size=(8, 2)), file_num_display_elem],
            #     [sg.Text('')]]
            
            # window['-CONTROLS-'].update(visible=True)
            window['-IMAGE-'].update(visible=True)
            window['-LISTBOX-'].update(values=fnames)
            window['-FILE_NUM-'].update(f'File 1 of {num_files}')
            window['-IMAGE_ELEM-'].update(data=get_img_data(filename, first=True))

            # window['-CONTROLS-'].update(layout=folder_browser + files + session + timer_layout)

        elif folder:
            print(f'start_time:{start_time}\ncurrent_time: {current_time}\nend_time: {end_time}\ntime_diff: {time_diff}\n')

            if event in MODES_KEYS:
                for choice in range(len(MODES_KEYS)):
                    if values[MODES_KEYS[choice]]:
                        session_mode = Session_Mode(choice)
                        new_layout = MODES_VALUES[choice]
                        for lay in MODES_VALUES:
                            window[lay].update(visible=False)
                        window[new_layout].update(visible=True)
                        break
                print(session_mode)

            if session_mode == Session_Mode.CONSTANT:
                pass
            elif session_mode == Session_Mode.CLASS:
                pass
            elif session_mode == Session_Mode.CUSTOM:
                if event == '-DEC-TIMER-':
                    if next_timeout > 6000:
                        next_timeout -= 6000
                        if next_timeout // 6000 > 1:
                            s = 's'
                        else:
                            s = ''
                        # TODO fix current timeout display
                        new_text = f"Current timeout: {next_timeout // 6000} Minute{s}"
                        print(new_text)
                        window['-CUR-TIMEOUT-'].update(value=new_text)
                elif event == '-INC-TIMER-':
                    if next_timeout < 6000 * 60:
                        next_timeout += 6000
                        if next_timeout // 6000 > 1:
                            s = 's'
                        else:
                            s = ''

                        # TODO fix current timeout display
                        new_text = f"Current timeout: {next_timeout // 6000} Minute{s}"
                        print(new_text)
                        window['-CUR-TIMEOUT-'].update(value=new_text)

            if event == '-RESET-':
                current_time = start_time = time_as_int()
                end_time = current_time + next_timeout
                time_diff = next_timeout
                print("pressed reset button")
            elif event == '-RUN-PAUSE-':
                print("pressed run-pause button")
                paused = not paused
                print(f"paused: {paused}")
                if paused:
                    time_diff = end_time - current_time
                else:
                    start_time = time_as_int() 
                    current_time = start_time
                    end_time = start_time + time_diff
                    print(f'start_time:{start_time}\ncurrent_time: {current_time}\nend_time: {end_time}\ntime_diff: {time_diff}\n')
                # Change button's text
                window['-RUN-PAUSE-'].update('Run' if paused else 'Pause')

            if event == '-NEXT-': #in ('-NEXT-', 'Down:40', 'Next:34'):
                img += 1
                if img >= num_files:
                    img -= num_files
                filename = os.path.join(folder, fnames[img])
                current_time = 0
            elif event == '-PREV-': #in ('-PREV-', 'Up:38', 'Prior:33'):
                img -= 1
                if img < 0:
                    img += num_files
                filename = os.path.join(folder, fnames[img])
                current_time = 0
            elif event == '-LISTBOX-':              # something from the listbox
                f = values['-LISTBOX-'][0]          # selected filename
                filename = os.path.join(folder, f)  # read this file
                img = fnames.index(f)                 # update running index
            else:
                filename = os.path.join(folder, fnames[img])
            
            print(f'start_time:{start_time}\ncurrent_time: {current_time}\nend_time: {end_time}\ntime_diff: {time_diff}\n')
            if time_diff <= 50 and not paused:
                print("\n\n\nRESET\n\n\n")
                current_time = start_time = time_as_int()
                end_time = current_time + next_timeout
                time_diff = next_timeout
                img += 1
                if img >= num_files:
                    img %= num_files
                filename = os.path.join(folder, fnames[img])
            elif time_diff > 0 and not paused:
                print("\n\n\nTIMER RUNNING\n\n\n")
                current_time = time_as_int()
                time_diff = end_time - current_time
            print(f'start_time:{start_time}\ncurrent_time: {current_time}\nend_time: {end_time}\ntime_diff: {time_diff}\n')

            # if current_time > NEXTIMGTIMEOUT:
            #     print("\n\n\nRESET\n\n\n")
            #     paused_time = start_time = time_as_int()
            #     current_time = 0
            #     img += 1
            #     if img >= num_files:
            #         img %= num_files
            #     filename = os.path.join(folder, fnames[img])

            # --------- Display timer in window --------
            # window['-TIMER-'].update('{:02d}:{:02d}'.format((current_time // 100) // 60,
            #                                             (current_time // 100) % 60))
            window['-TIMER-'].update('{:02d}:{:02d}'.format(((time_diff) // 100) // 60,
                                                        ((time_diff) // 100) % 60))

            # update window with new image
            image_elem.update(data=get_img_data(filename, first=True))
            window['-IMAGE_ELEM-'].update(data=get_img_data(filename, first=True))
            # update page display
            # file_num_display_elem.update('File {} of {}'.format(i+1, num_files))
            window.Refresh()

    window.close()

if __name__ == "__main__":
    main()
