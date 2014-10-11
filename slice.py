import os
import sys
import subprocess
import shutil
import json
import re
from distutils.spawn import find_executable

if not len(sys.argv) == 3:
    print "Proper usage: python slice.py [.sketch file] [.xcassets file]"
    exit(1)

INPUT_FILE = os.path.abspath(sys.argv[1])
if not os.path.exists(INPUT_FILE):
    print "Sketch file %s does not exist" % INPUT_FILE
    exit(1)
if not INPUT_FILE.endswith('.sketch'):
    print "Input file is expected to be a .sketch file"
    exit(1)

ASSETS_FILE = os.path.abspath(sys.argv[2])
if not os.path.exists(ASSETS_FILE):
    print "Assets bundle %s does not exist" % ASSETS_FILE
    exit(1)
if not ASSETS_FILE.endswith('.xcassets'):
    print "Output file is expected to be a .xcassets bundle"
    exit(1)

OUTPUT_DIR = os.path.join(ASSETS_FILE, 'Slices')

# clear the output directory

print "Creating output directory"

if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR)

# export slices

sketchtool_executable = find_executable("sketchtool")
if sketchtool_executable is None:
    # Xcode overrides $PATH no matter how you've configured it
    # sketchtool is by default installed into /usr/local/bin, so let's check there
    supposed_executable = '/usr/local/bin/sketchtool'
    if os.path.exists(supposed_executable):
        sketchtool_executable = supposed_executable

if sketchtool_executable is None:
    print 'Please install sketchtool'
    exit(1)

print "Exporting slices from", INPUT_FILE, "to", ASSETS_FILE

subprocess.call([
    sketchtool_executable,
    'export',
    'slices',
    INPUT_FILE,
    '--output=' + OUTPUT_DIR,
])

# define the asset model

class Asset(object):
    def __init__(self, path):
        self.path = path
        self.filename = path.rpartition("/")[2]
        regex_match = re.search("(\\w+)@?(.*?)\\.(.+)", filename, re.S)
        self.name = regex_match.group(1)
        scale = regex_match.group(2)
        if len(scale) == 0:
            scale = '1x'
        self.scale = scale
        self.extension = regex_match.group(3)

    def info(self):
        return {
            'idiom': 'universal',
            'scale': self.scale,
            'filename': self.filename,
        }

# group slices into sets of assets

print "Grouping assets"

slices = {}
for filename in os.listdir(OUTPUT_DIR):
    asset_path = os.path.join(OUTPUT_DIR, filename)
    asset = Asset(asset_path)
    assets_for_slice_name = slices.get(asset.name, [])
    assets_for_slice_name.append(asset)
    slices[asset.name] = assets_for_slice_name

# move assets into imagesets

print "Generating imagesets"

for slice_name, assets in slices.iteritems():
    imageset_name = slice_name + ".imageset"
    imageset_directory = os.path.join(OUTPUT_DIR, imageset_name)
    os.makedirs(imageset_directory)
    imageset_info = {
        'images': [],
        'info': {
            'version': 1,
            'author': 'xcode',
        },
    }
    for asset in assets:
        shutil.move(asset.path, imageset_directory)
        imageset_info['images'].append(asset.info())
    imageset_info_file_path = os.path.join(imageset_directory, 'Contents.json')
    imageset_info_file = open(imageset_info_file_path, 'w+')
    imageset_info_file.write(json.dumps(imageset_info))
    imageset_info_file.close()

print "Slices added to ", ASSETS_FILE

