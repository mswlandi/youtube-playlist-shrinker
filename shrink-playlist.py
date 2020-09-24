from pytube import Playlist, YouTube
import re
import os
import sys, getopt
import subprocess
import threading

def editDefaultProgramParameterValue(parameter, value):
    programLines = open(__file__).read().split('\n')
    with open(__file__, 'w') as programFile:
        newProgramLines = []
        for line in programLines:
            if line.startswith(parameter + ' = \''):
                newProgramLines.append(parameter + ' = \'' + value + '\'')
            else:
                newProgramLines.append(line)
        programFile.write('\n'.join(newProgramLines))

def askForOverwrite(file):
    while True:
        command = input(f'Overwrite file {video}? (Y/N)\n')
        if command.lower() in ['y','yes']:
            return True
        elif command.lower() in ['n','no']:
            return False

def isFirstSubsetOfSecond(first, second):
    positionInFirst = 0
    for letter in second:
        if letter == first[positionInFirst]:
            positionInFirst += 1
    return positionInFirst == len(first)

def downloadVideo(o, url):
    while True:
        try:
            video = YouTube(url)
            video.streams.get_highest_resolution().download(o)
            break
        except:
            continue

def shrinkVideo(o, video, arguments, muted):
    if muted:
        subprocess.run(f'auto-editor "{o}/{video}" {arguments} --no_open -o "{o}/_{video}"', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        subprocess.run(f'auto-editor "{o}/{video}" {arguments} --no_open -o "{o}/_{video}"')
    os.remove(f'{o}/{video}')
    os.rename(f'{o}/_{video}', f'{o}/{video}')

o = './processed/'
v = '2.2'
s = '22'
m = '6'
t = '1'
parameters = sys.argv[1:]

try:
    opts, args = getopt.getopt(parameters[1:],'hv:s:m:t:',['sounded_speed=', 'silent_speed=', 'margin=', 'threads='])
    l = parameters[0]
except:
    try:
        parameters = input('Parameters: ').split(' ')
        opts, args = getopt.getopt(parameters[1:],'hv:s:m:t:',['sounded_speed=', 'silent_speed=', 'margin=', 'threads='])
        l = parameters[0]
    except:
        print('shrink-playlist.py <inputfile> [-v <sounded speed>] [-s <silent speed>] [-m <margin>] [-t <number of threads>]')
        sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print('shrink-playlist.py <inputfile> [-v <sounded speed>] [-s <silent speed>] [-m <margin>] [-t <number of threads>]')
        sys.exit()
    elif opt in ('-v', '--sounded_speed'):
        v = arg
        editDefaultProgramParameterValue('v', v)
    elif opt in ('-s', '--silent_speed'):
        s = arg
        editDefaultProgramParameterValue('s', s)
    elif opt in ('-m', '--margin'):
        m = arg
        editDefaultProgramParameterValue('m', m)
    elif opt in ('-t', '--threads'):
        t = arg
        editDefaultProgramParameterValue('t', t)

arguments = f'-v {v} -s {s} -m {m}'

if 'playlist?' not in l:
    if os.path.exists(o+'temp/'):
        for video in os.listdir(o+'temp/'):
            os.remove(o+'temp/'+video)
        os.rmdir(o+'temp/')
    os.makedirs(o+'temp/')
    print(f'\nDownloading: \n{l}\n')
    downloadVideo(o+'temp/', l)
    video = os.listdir(o+'temp/')[0]
    try:
        os.rename(o+'temp/'+video, o+video)
    except:
        if askForOverwrite(video):
            os.remove(o+video)
            os.rename(o+'temp/'+video, o+video)
        else:
            os.remove(o+'temp/'+video)
            os.rmdir(o+'temp/')
            sys.exit(3)
    os.rmdir(o+'temp/')
    videoName = '.'.join(video.split('.')[:-1])
    print(f'\nShrinking: \n{videoName}\n')
    shrinkVideo(o, video, arguments, False)
    sys.exit(0)

playlist = Playlist(l)

# YouTube updated their HTML so the regex that Playlist uses to find the videos is currently outdated
playlist._video_regex = re.compile(r'\"url\":\"(/watch\?v=[\w-]*)')

if not os.path.exists(f'{o}'):
    os.makedirs(f'{o}')

print(f'\nDownloading {len(playlist.video_urls)} videos from {playlist.title()}:\n')

for index in range(0, len(playlist.video_urls), int(t)):
    threads = []
    videoURLs = '\n'.join(playlist.video_urls[index:index+int(t)])
    print(f'\nDownloading: \n{videoURLs}\n')
    for videoURL in playlist.video_urls[index:index+int(t)]:
        threads.append(threading.Thread(target=downloadVideo, args=(f'{o}/{playlist.title()}', videoURL)))
        threads[-1].start()
    for thread in threads:
        thread.join()

o += sorted([p for p in os.listdir(f'{o}') if os.path.isdir(o+p) and isFirstSubsetOfSecond(p, playlist.title())], key=lambda p: -len(p))[0]

videos = os.listdir(f'{o}')
for index in range(0, len(videos), int(t)):
    threads = []
    videoNames = '\n'.join(['.'.join(video.split('.')[:-1]) for video in videos[index:index+int(t)]])
    print(f'\nShrinking: \n{videoNames}\n')
    for video in videos[index:index+int(t)]:
        threads.append(threading.Thread(target=shrinkVideo, args=(o, video, arguments, int(t) != 1)))
        threads[-1].start()
    for thread in threads:
        thread.join()