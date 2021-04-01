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
        command = input(f'Overwrite file {file}? (Y/N)\n')
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

def is_first_subset_of_second(first, second):
    position_in_first = 0
    for letter in second:
        if letter == first[position_in_first]:
            position_in_first += 1
    return position_in_first == len(first)

def download_video(download_folder, video_url):
    print(f'\nDownloading: \n{video_url}\n')
    while True:
        try:
            video = YouTube(video_url)
            video.streams.get_highest_resolution().download(download_folder)
            break
        except:
            continue
    print(f'\nDownloaded: \n{video_url}\n')

def shrink_video(video_name_with_extension, muted):
    global output_folder, arguments

    video_name = '.'.join(video_name_with_extension.split('.')[:-1])
    output_path = join_path(output_folder, video_name_with_extension)
    output_temp_path = join_path(output_folder, '_' + video_name_with_extension)
    print(f'\nShrinking: \n{video_name}\n')
    if muted:
        subprocess.run(f'auto-editor "{output_path}" {arguments} --no_open -o "{output_temp_path}"', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        subprocess.run(f'auto-editor "{output_path}" {arguments} --no_open -o "{output_temp_path}"')
    os.remove(f'{output_path}')
    os.rename(f'{output_temp_path}', f'{output_path}')
    print(f'\nShrinked: \n{video_name}\n')

def process_youTube_playlist(url_or_path):
    global output_folder, number_of_threads

    playlist = Playlist(url_or_path)

    # YouTube updated their HTML so the regex that Playlist uses to find the videos is currently outdated
    playlist._video_regex = re.compile(r'\"url\":\"(/watch\?v=[\w-]*)')

    if not exists_path(f'{output_folder}'):
        os.makedirs(f'{output_folder}')

    download_folder = join_path(output_folder, playlist.title)

    print(f'\nDownloading {len(playlist.video_urls)} videos from {playlist.title} (YouTube playlist) in {download_folder}\n')

    threads = []
    threads_semaphore = Semaphore(number_of_threads)
    for video_url in playlist.video_urls:
        threads.append(Thread(target=run_thread, args=(download_video, (download_folder, video_url), threads_semaphore)))
        threads[-1].start()
    for thread in threads:
        thread.join()

    output_folder = download_folder

    processes_local_playlist(download_folder)

def process_youtube_video(url_or_path):
    global output_folder

    output_temp_folder = reset_temp_folder(output_folder)

    download_folder = output_temp_folder
    download_video(download_folder, url_or_path)
    processes_local_playlist(download_folder)

    shutil.rmtree(output_temp_folder)

def processes_local_playlist(url_or_path, muted=False):
    global number_of_threads

    folder_filenames = list(os.listdir(url_or_path))

    if not muted:
        print(f'\nObtaining {len(folder_filenames)} videos from {url_or_path} in {output_folder}\n')
        print('\n'.join(folder_filenames))

    threads = []
    threads_semaphore = Semaphore(number_of_threads)
    for filename in folder_filenames:
        threads.append(Thread(target=run_thread, args=(process_local_video, (join_path(url_or_path, filename), min(number_of_threads, len(folder_filenames)) <= 1), threads_semaphore)))
        threads[-1].start()
    for thread in threads:
        thread.join()

def process_local_video(url_or_path, muted=False):
    global output_folder

    video_name_with_extension = split_path(url_or_path)[1]
    output_path = join_path(output_folder, video_name_with_extension)

    if exists_path(output_path):
        if ask_for_overwrite(video_name_with_extension):
            shutil.copy(url_or_path, output_path)
            shrink_video(video_name_with_extension, muted)


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