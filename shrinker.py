from pytube import Playlist, YouTube
from threading import Thread, Semaphore
from os.path import join as join_path, split as split_path, exists as exists_path, isdir as is_dir_path
import re
import os
import shutil
import sys, getopt
import subprocess
import json

def load(filename):
    try:
        dataFile = open(filename + '.json', 'r')
        data = json.loads(dataFile.read())
        dataFile.close()
        return data
    except:
        return None

def save(filename, data):
    dataFile = open(filename + '.json', 'w')
    dataFile.write(json.dumps(data))
    dataFile.close()

def run_thread(function_to_run, function_to_run_args, threads_semaphore: Semaphore):
    threads_semaphore.acquire()
    function_to_run(*function_to_run_args)
    threads_semaphore.release()

def ask_for_overwrite(file):
    while True:
        command = input(f'\nOverwrite file {file}? (Y/N)\n')
        if command.lower() in ['y','yes']:
            return True
        elif command.lower() in ['n','no']:
            return False

def reset_temp_folder(output_folder):
    output_temp_folder = join_path(output_folder, 'temp/')
    if exists_path(output_temp_folder):
        for filename in os.listdir(output_temp_folder):
            os.remove(join_path(output_temp_folder, filename))
        os.rmdir(output_temp_folder)
    os.makedirs(output_temp_folder)
    return output_temp_folder

def download_youtube_video(download_folder, youtube_video):
    print(f'\nDownloading \"{youtube_video.title}\"...')
    while True:
        try:
            youtube_video.streams.get_highest_resolution().download(download_folder)
            break
        except:
            continue
    print(f'\nDownloaded \"{youtube_video.title}\".')

def shrink_video(source_path, output_path, muted, mode): # Mode may be "remove source or override others files", "remove source but not override other files" or "neither remove source nor override other files"
    global arguments

    source_folder, video_source_name_with_extension = split_path(source_path)
    video_source_name = '.'.join(video_source_name_with_extension.split('.')[:-1])
    print(f'\nShrinking \"{video_source_name}\"...')

    if os.path.relpath(source_path, output_path) == '.': # If the source_path and the output_path are the same...
        if mode in ['neither remove source nor override other files'] and not ask_for_overwrite(source_path):
            print(f'\nFailed to shrink \"{video_source_name}\".')
            return
        new_source_path = join_path(source_folder, '_' + video_source_name_with_extension)
        if exists_path(new_source_path):
            if mode in ['remove source but not override other files', 'neither remove source nor override other files'] and not ask_for_overwrite(new_source_path):
                print(f'\nFailed to shrink \"{video_source_name}\".')
                return
            os.remove(new_source_path)
        shutil.move(source_path, new_source_path)
        source_path = new_source_path
        mode = 'remove source but not override other files'

    if exists_path(output_path):
        if mode in ['remove source but not override other files', 'neither remove source nor override other files'] and not ask_for_overwrite(output_path):
            print(f'\nFailed to shrink \"{video_source_name}\".')
            return
        os.remove(output_path)

    if muted:
        subprocess.run(f'auto-editor "{source_path}" {arguments} --no_open -o "{output_path}"', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        subprocess.run(f'auto-editor "{source_path}" {arguments} --no_open -o "{output_path}"')

    if mode in ['remove source or override others files', 'remove source but not override other files']:
        os.remove(source_path)
        if len(os.listdir(source_folder)) == 0:
            os.rmdir(source_folder)

    print(f'\nShrinked \"{video_source_name}\".')

def process_youTube_playlist(youtube_playlist_url):
    global output_folder, number_of_threads

    youtube_playlist = Playlist(youtube_playlist_url)

    # YouTube updated their HTML so the regex that Playlist uses to find the videos is currently outdated
    youtube_playlist._video_regex = re.compile(r'\"url\":\"(/watch\?v=[\w-]*)')

    if not exists_path(f'{output_folder}'):
        os.makedirs(f'{output_folder}')

    download_folder = join_path(output_folder, youtube_playlist.title)
    if exists_path(download_folder):
        input(f'\nDownload output folder \"{download_folder}\" already exists.\n - To avoid conflicts of re-shrinking or overriding files, please close the program or rename the existing folder before continuing.\n - If you want to continue without closing, press enter.')

    print(f'\nDownloading {len(youtube_playlist.video_urls)} videos from \"{youtube_playlist.title}\" (YouTube playlist) in \"{download_folder}\".')

    threads = []
    threads_semaphore = Semaphore(number_of_threads)
    for youtube_video_url in youtube_playlist.video_urls:
        youtube_video = YouTube(youtube_video_url)
        threads.append(Thread(target=run_thread, args=(download_youtube_video, (download_folder, youtube_video), threads_semaphore)))
        threads[-1].start()
    for thread in threads:
        thread.join()

    output_folder = download_folder

    processes_local_playlist(download_folder, True, 'remove source but not override other files')

def process_youtube_video(youtube_video_url):
    global output_folder

    output_temp_folder = reset_temp_folder(output_folder)

    download_folder = output_temp_folder
    youtube_video = YouTube(youtube_video_url)
    download_youtube_video(download_folder, youtube_video)
    processes_local_playlist(download_folder, True, 'remove source but not override other files')

def processes_local_playlist(source_path, muted=False, mode='neither remove source nor override other files'):
    global number_of_threads

    folder_filenames = list(os.listdir(source_path))

    if not muted:
        print(f'\nObtaining {len(folder_filenames)} videos from \"{source_path}\" in \"{output_folder}\".')
        for filename in folder_filenames:
            print(filename)

    threads = []
    threads_semaphore = Semaphore(number_of_threads)
    for filename in folder_filenames:
        threads.append(Thread(target=run_thread, args=(process_local_video, (join_path(source_path, filename), min(number_of_threads, len(folder_filenames)) > 1, mode), threads_semaphore)))
        threads[-1].start()
    for thread in threads:
        thread.join()

def process_local_video(source_path, muted=False, mode='neither remove source nor override other files'):
    global output_folder

    video_name_with_extension = split_path(source_path)[1]
    output_path = join_path(output_folder, video_name_with_extension)

    shrink_video(source_path, output_path, muted, mode)


if __name__ == '__main__':
    try:
        output_folder, sounded_video_speed, muted_video_speed, margin_size, number_of_threads = load('config')
    except:
        output_folder, sounded_video_speed, muted_video_speed, margin_size, number_of_threads = ('./processed/', '1.5', '15', '6', '4')

    parameters = sys.argv[1:]

    if len(parameters) > 0:
        url_or_path = parameters[0]
        try:
            opts, args = getopt.getopt(parameters[1:],'hv:s:m:t:',['sounded_speed=', 'silent_speed=', 'margin=', 'threads='])
        except:
            print('shrink-playlist.py <inputfile> [-v <sounded speed>] [-s <silent speed>] [-m <margin>] [-t <number of threads>]')
            sys.exit(2)

        for opt, arg in opts:
            if opt == '-h':
                print('shrink-playlist.py <inputfile> [-v <sounded speed>] [-s <silent speed>] [-m <margin>] [-t <number of threads>]')
                sys.exit()
            elif opt in ('-v', '--sounded_speed'):
                sounded_video_speed = arg
            elif opt in ('-s', '--silent_speed'):
                muted_video_speed = arg
            elif opt in ('-m', '--margin'):
                margin_size = arg
            elif opt in ('-t', '--threads'):
                number_of_threads = arg
    else:
        url_or_path = input(f'YouTube video/playlist link or Local video/folder path (you can drag it here): ')

        temp = input(f'Video speed when with sound (ENTER to default = {sounded_video_speed}x): ')
        sounded_video_speed = temp if temp != '' else sounded_video_speed

        temp = input(f'Video speed when silence (ENTER to default = {muted_video_speed}x): ')
        muted_video_speed = temp if temp != '' else muted_video_speed

        temp = input(f'Silence parts margins (ENTER to default = {margin_size} frames): ')
        margin_size = temp if temp != '' else margin_size

        temp = input(f'Number of threads (ENTER to default = {number_of_threads} threads): ')
        number_of_threads = temp if temp != '' else number_of_threads

    url_or_path = url_or_path.strip('\"')
    number_of_threads = int(number_of_threads)

    arguments = f'-v {sounded_video_speed} -s {muted_video_speed} -m {margin_size}'
    save('config', (output_folder, sounded_video_speed, muted_video_speed, margin_size, number_of_threads))

    if 'youtube.com' in url_or_path or 'youtu.be' in url_or_path:
        if 'playlist?' in url_or_path:
            process_youTube_playlist(url_or_path)
        else:
            process_youtube_video(url_or_path)
    else:
        if '.' in split_path(url_or_path)[1]:
            process_local_video(url_or_path)
        else:
            processes_local_playlist(url_or_path)