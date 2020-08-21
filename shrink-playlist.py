from pytube import Playlist, YouTube
import re
import os
import sys, getopt

def editDefaultProgramParameterValue(parameter, value):
    programLines = open(__file__).read().split('\n')
    with open(__file__, 'w') as programFile:
        newProgramLines = []
        print(__file__)
        for line in programLines:
            if parameter + ' = \'' in line:
                newProgramLines.append(line.split('=')[0] + '= \'' + value + '\'')
            else:
                newProgramLines.append(line)
        programFile.write('\n'.join(newProgramLines))


s = '10'
v = '1'
m = '2'
parameters = sys.argv[1:]
processedFolder = "processed"

try:
    opts, args = getopt.getopt(parameters[1:],"hv:s:m:",["sounded_speed=", "silent_speed=", "margin="])
    l = parameters[0]
except:
    try:
        parameters = input('Parameters: ').split(' ')
        opts, args = getopt.getopt(parameters[1:],"hv:s:m:",["sounded_speed=", "silent_speed=", "margin="])
        l = parameters[0]
    except:
        print('shrink-playlist.py <inputfile> -v <sounded speed> -s <silent speed> -m <margin>')
        sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print('shrink-playlist.py <inputfile> -v <sounded speed> -s <silent speed> -m <margin>')
        sys.exit()
    elif opt in ("-v", "--sounded_speed"):
        v = arg
        editDefaultProgramParameterValue('v', v)
    elif opt in ("-s", "--silent_speed"):
        s = arg
        editDefaultProgramParameterValue('s', s)
    elif opt in ("-m", "--margin"):
        m = arg
        editDefaultProgramParameterValue('m', m)

playlist = Playlist(l)

arguments = f'-v {v} -s {s} -m {m}'

# YouTube updated their HTML so the regex that Playlist uses to find the videos is currently outdated
playlist._video_regex = re.compile(r"\"url\":\"(/watch\?v=[\w-]*)")

if not os.path.exists(f'{processedFolder}'):
    os.makedirs(f'{processedFolder}')
currentDirs = [p for p in os.listdir(f"{processedFolder}") if os.path.isdir(f"{processedFolder}/{p}")]
print(currentDirs)

print(f'\nDownloading {len(playlist.video_urls)} videos from {playlist.title()}:\n')
for url in playlist.video_urls:
    print(url)
    video = YouTube(url)
    video.streams.get_highest_resolution().download(f"{processedFolder}/{playlist.title()}")

folder = [p for p in os.listdir(f"{processedFolder}") if os.path.isdir(f"{processedFolder}/{p}") and p not in currentDirs][0]

for video in os.listdir(f"{processedFolder}/{folder}"):
    videoName = '.'.join(video.split('.')[:-1])
    print(f'\nShrinking {videoName}:\n')
    os.system(f'auto-editor "{processedFolder}/{folder}/{video}" {arguments} --no_open -o "{processedFolder}/{folder}/_{video}"')
    os.remove(f'{processedFolder}/{folder}/{video}')
    os.rename(f'{processedFolder}/{folder}/_{video}', f'{processedFolder}/{folder}/{video}')