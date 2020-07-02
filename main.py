import argparse
import mutagen
import pathlib
import subprocess
import sys

argparser = argparse.ArgumentParser()
argparser.add_argument("input")
argparser.add_argument("-c", "--cover")
argparser.add_argument("-y", "--overwrite", action="store_true")
args = argparser.parse_args()

def get_tag(mutagen_file, tag):
    try:
        return mutagen_file.tags[tag].text[0]
    except KeyError:
        return {
            "TPE1": "[unknown artist]",
            "TPE2": "[unknown artist]",
            "TALB": "[untitled]"
        }[tag]  # dumb hack i know but i will straight up not be reading other fields i think

def is_homogenous(l):
    return l.count(l[0]) == len(l)

def most_common(l):
    count_dict = {}
    for i in l:
        if i in count_dict:
            continue
        else:
            count_dict[i] = l.count(i)//2
    return [i for i in count_dict.keys() if count_dict[i] == max(count_dict.values())]

cmd = "python3 convert.py -i {} -o ./.out".format(args.input)
if args.cover:
    cmd += " -c " + args.cover
if args.overwrite:
    cmd += " -y"

subprocess.run(cmd, shell=True)
subprocess.run("python3 finish.py", shell=True)
