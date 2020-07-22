# just straight up piracy i have stolen six televisions

# hopefully the help menus are enough help

# to add (cool joke) :
# make this a website sometime without any fuckin dumbass watermark like all the other ones use

import argparse
import filetype
import hashlib
import mutagen
import pathlib
import shlex
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", default=".", nargs="*", help="the item to make into a video. can be either a folder or file. if not specified, this will be every sound file in the directory in which this file resides, and you will be given a confirmation prompt. you may specify multiple items")
parser.add_argument("-o", "--output", default=".", help="the path of the file or directory in which the video(s) will be located after conversion. if not specified, this will be the directory in which this file resides, and you will be given a confirmation prompt")
parser.add_argument("-c", "--cover", default="", nargs="*", help="the path of the image that will be shown for the duration of the video. if not specified, the program will use the image in the specified file's tags, and if there is no such image, an error will return. if multiple input items are specified, there must be either one cover per input item, or one cover which will be applied to every input item")
parser.add_argument("-y", "--overwrite", action="store_true", help="skip the overwrite prompt and overwrite any files with conflicting names")
parser.add_argument("-n", "--no-overwrite", action="store_true", help="skip the overwrite prompt and do not overwrite any files with conflicting names")

args = parser.parse_args()


excluded_audio_types = ["midi", "amr"]
excluded_image_types = ["jpx", "canon", "photo", "heic", "bmp", "tiff"]

def is_audio(path): # excludes midi and whatever "amr" is
    abspath = str(path.resolve())
    mime = filetype.guess(abspath).mime
    return "audio/" in mime and all([n not in mime for n in excluded_audio_types])

def is_image(path): # excludes a bunch of image types i have arbitrarily considered to be unreliable
    abspath = str(path.resolve())
    mime = filetype.guess(abspath).mime
    return "image/" in mime and all([n not in mime for n in excluded_image_types])

def get_cover(mutagen_file):
    tags = mutagen_file.tags
    for key in tags.keys():
        if "APIC" in key:
            return tags[key].data
    return "NOCOVER"

def get_tag(mutagen_file, tag):
    try:
        return mutagen_file.tags[tag].text[0]
    except KeyError:
        return {
            "TPE1": "[unknown artist]",
            "TIT2": "[untitled]",
            "TRCK": ""
        }[tag]  # dumb hack i know but i will straight up not be reading other fields i think

def out_format(audio_file):
    filename = audio_file.stem
    mutagen_file = mutagen.File(str(audio_file))
    artist_name = get_tag(mutagen_file, "TPE1").replace("/", "⧸") # replacing actual "/" with division symbol in filename because you cant have slashes in filenames DUMBASS
    track_title = get_tag(mutagen_file, "TIT2").replace("/", "⧸")
    track_number = get_tag(mutagen_file, "TRCK").split("/")[0]
    
    if artist_name == "[unknown artist]":
        _artist_name = input("there is no artist information in the file '{}'. enter an artist name or, if this is correct and the artist is unknown, type nothing and hit enter".format(str(audio_file)))
        if _artist_name:
            artist_name = _artist_name 
    
    if track_title == "[untitled]":
        _track_title = input("the track in the file '{}' has no name. enter a track name or, if this is correct and the song has no name / its name is unknown, type nothing and hit enter".format(str(audio_file)))
        if _track_title:
            track_title = _track_title
    
    if track_number == "":
        track_number = input("the track in the file '{}' has no number. enter a track number or hit enter to leave it unspecified".format(str(audio_file)))
    if track_number:
        track_number += " "
    return "{}{} - {}".format(track_number, artist_name, track_title)


input_paths = args.input
files_to_convert = []
for _input_path in input_paths:
    input_path = pathlib.Path(_input_path).expanduser()
    if input_path.is_dir():
        for path in input_path.iterdir():
            if is_audio(path):
                files_to_convert.append(path.resolve())
    elif input_path.exists():
        if is_audio(input_path):
            files_to_convert.append(input_path.resolve())
    else:
        parser.error("file or folder at path '{}' does not exist".format(str(input_path.resolve())))


output_path = pathlib.Path(args.output).expanduser()
if not output_path.exists():
    output_path.mkdir(parents=True, exist_ok=True)
output_path = output_path.resolve()


cover_mode = ""
cover_paths = []
if len(args.cover) == 0:
    cover_mode = "individual"
else:
    for cover in args.cover:
        cover_path = pathlib.Path(cover).expanduser()
        
        if not cover_path.exists():
            parser.error("file at path '{}' does not exist".format(str(cover_path.resolve())))
            break
        if not is_image(cover_path):
            parser.error("file at path '{}' is not an image and cannot be used for cover art".format(str(cover_path.resolve())))
            break
        
        cover_paths.append(cover_path.resolve())
    if len(args.cover) == 1:
        cover_mode = "global"
    elif len(args.cover) == len(args.input_paths):
        cover_mode = "respective"
    else:
        parser.error("invalid number of cover art files specified. use either one for each input path, one total, or none")


for index, audio_file in enumerate(files_to_convert):
    output_file = output_path / (out_format(audio_file)+".mp4")
    cover_filename = ""    
    
    if cover_mode == "individual":
        mutagen_file = mutagen.File(str(audio_file))
        cover_art = get_cover(mutagen_file)
        if cover_art == "NOCOVER":
            parser.error("there is no cover art attached to the file '{}'. specify a cover with the -c option or modify the id3 tags to include cover art".format(str(audio_file)))
            break
        cover_filename = "." + hashlib.md5(cover_art).hexdigest()
        with open(cover_filename, 'wb') as cover_image:
            cover_image.write(cover_art)
        cover_path = pathlib.Path(cover_filename).expanduser()
        cover_extension = filetype.guess(cover_filename).extension
        cover_path.rename(cover_filename + "." + cover_extension)
        cover_filename += "." + cover_extension

    if cover_mode == "global":
        cover_filename = str(cover_paths[0])

    if cover_mode == "respective":
        cover_filename = str(cover_paths[index])

    ffmpegcmd = "ffmpeg{} -r 1 -loop 1 -i {} -i {} -acodec copy -r 1 -shortest -vcodec libx264 {}".format(
        " -y" if args.overwrite else (" -n" if args.no_overwrite else ""),
        shlex.quote(cover_filename),
        shlex.quote(str(audio_file)),
        shlex.quote(str(output_file))
    )
    print(ffmpegcmd)
    subprocess.run(ffmpegcmd, shell=True)
