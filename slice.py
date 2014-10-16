import os
import sys
import subprocess
import shutil
import json
import re
import time
from distutils.spawn import find_executable

################################################################################
# HELPERS
################################################################################

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_empty_directory(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def json_dict_for_file_path(file_path):
    if os.path.exists(file_path):
        return json.load(open(file_path, 'r'))
    return None

def write_dict_to_file_path(file_path, info):
    json_file = open(file_path, 'w+')
    json_file.write(json.dumps(info))
    json_file.close()

################################################################################
# MODELS
################################################################################

class AssetGroup(object):
    def __init__(self, name):
        self.name = name
        self.assets = []

    @property
    def imageset_directory(self):
        imageset_name = self.name + ".imageset"
        return os.path.join(OUTPUT_DIR, imageset_name)

    @property
    def imageset_info_file_path(self):
        return os.path.join(self.imageset_directory, 'Contents.json')

    @property
    def info(self):
        info = {
            'images': [],
            'info': {
                'version': '1',
                'author': 'Slicer',
            },
        }
        for asset in self.assets:
            info['images'].append(asset.info)
        return info

class Asset(object):
    def __init__(self, path):
        self.path = path
        self.filename = path.rpartition("/")[2]
        regex_match = re.search("([\\w\\s]+)@?(.*?)\\.(.+)", filename, re.S)
        self.group_name = regex_match.group(1)
        scale = regex_match.group(2)
        if len(scale) == 0:
            scale = '1x'
        self.scale = scale
        self.extension = regex_match.group(3)

    @property
    def info(self):
        return {
            'idiom': 'universal',
            'scale': self.scale,
            'filename': self.filename,
        }

################################################################################

# start timer

start_time = time.time()

# parse arguments

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

EXPORT_DIR = os.path.join(os.path.dirname(INPUT_FILE), 'tmp_exported_slices')
OUTPUT_DIR = os.path.join(ASSETS_FILE, 'Slices')
OUTPUT_INFO_PATH = os.path.join(OUTPUT_DIR, 'info.json')

# check to see if the sketch file has been modified

export_info = json_dict_for_file_path(OUTPUT_INFO_PATH)
if export_info:
    export_timestamp = export_info.get('timestamp')
    input_file_modification_timestamp = os.path.getmtime(INPUT_FILE)
    if export_timestamp > input_file_modification_timestamp:
        print 'Sketch file has not been modified; skipping export'
        exit(0)

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

print "Creating temporary export directory"
create_empty_directory(EXPORT_DIR)

print "Exporting slices"
subprocess.call([
    sketchtool_executable,
    'export',
    'slices',
    INPUT_FILE,
    '--output=' + EXPORT_DIR,
])

# group into sets of assets

print "Grouping assets"

asset_groups = {}
for filename in os.listdir(EXPORT_DIR):
    asset_path = os.path.join(EXPORT_DIR, filename)
    asset = Asset(asset_path)
    asset_group = asset_groups.get(asset.group_name)
    if asset_group is None:
        asset_group = AssetGroup(asset.group_name)
        asset_groups[asset.group_name] = asset_group
    asset_group.assets.append(asset)

# move assets into imagesets

print "Creating output directory"
create_empty_directory(OUTPUT_DIR)

print "Generating imagesets"

for asset_group in asset_groups.values():
    # create the imageset
    imageset_directory = os.path.join(OUTPUT_DIR, asset_group.name + '.imageset')
    create_empty_directory(imageset_directory)
    # place the assets in the imageset
    for asset in asset_group.assets:
        shutil.move(asset.path, imageset_directory)
    # write the imageset info
    imageset_info_file_path = os.path.join(imageset_directory, 'Contents.json')
    write_dict_to_file_path(imageset_info_file_path, asset_group.info)

# save the export timestamp

write_dict_to_file_path(OUTPUT_INFO_PATH, {'timestamp': time.time()})

# delete the temporary export directory

print 'Deleting temporary export directory'
shutil.rmtree(EXPORT_DIR)

# print the time

time_elapsed = time.time() - start_time
print 'Finished in %f seconds' % time_elapsed

