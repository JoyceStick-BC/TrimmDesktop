import requests
import zipfile
import os
import json
import shutil

from tqdm import tqdm

# installs unzipped package to the given directory
def download(bundlename, version, path):
    url = "http://trimm3d.com/download/" + bundlename + ""
    if version is not None:
        url += "/" + str(version)

    print("Downloading " + bundlename + "!")
    returned_request = requests.get(url, stream=True)
    total_size = int(returned_request.headers.get('content-length', 0))/(32*1024)

    with open('output.bin', 'wb') as f:
        for data in tqdm(returned_request.iter_content(32 * 1024), total=total_size, unit='B', unit_scale=True):
            f.write(data)

    # make sure web response is good before continuing
    if returned_request.status_code != 200:
        print("Bad response for url: %s" % url)
        os.remove("output.bin")
        return

    # make sure we have a zip file
    if not zipfile.is_zipfile("output.bin"):
        print("Returned file is not a zip at url: %s" % url)
        os.remove("output.bin")
        return

    print("Successfully downloaded " + bundlename + "!")

    # create a zipfile object
    zip_file = zipfile.ZipFile("output.bin")

    # get root trimm info.json if it exists, else create one
    trimm_path = os.path.join(path, "trimm.json")
    trimm_json = {"assets": {}, "packages": {}}
    if os.path.isfile(trimm_path):
        data_file = open(trimm_path, 'r')
        trimm_json = json.load(data_file)
    trimm_assets = trimm_json["assets"]
    trimm_packages = trimm_json["packages"]

    downloading_path = os.path.join(path, "downloading")
    zip_file.extractall(downloading_path)

    # let's delete the old bundle if it exists
    bundle_path = os.path.join(path, bundlename)
    if os.path.exists(bundle_path):
        shutil.rmtree(bundle_path)

    info_jsons = []
    drill(downloading_path, path, info_jsons)

    # let's go over all the jsons and add them to our trimm.json
    for info_json in info_jsons:
        if info_json["type"] == "asset":
            trimm_assets[bundlename] = info_json["version"]  # TODO could have multiple bundlenames, so loop through this
        elif info_json["type"] == "package":
            trimm_packages[bundlename] = info_json["version"]

    # delete the downloading folder and output.bin
    zip_file.close()
    os.remove("output.bin")
    shutil.rmtree(downloading_path)
    print "downloading_path line 71: " + downloading_path

    # dump json
    with open(trimm_path, 'w+') as out_file:
        json.dump(trimm_json, out_file, indent=4, sort_keys=True)

    print("Successfully installed " + bundlename + "!")


def drill(download_path, vendor_path, info_jsons):
    # let's get all the files in the downloading path
    for filename in os.listdir(download_path):
        file_in_downloading_path = os.path.join(download_path, filename)
        # if we find a file
        dumbvariablewedontneed, file_extension = os.path.splitext(file_in_downloading_path)
        if file_extension == ".zip":
            # let's look for zips in this dir by identifying any info.jsons
            for downloaded_file in os.listdir(download_path):
                downloaded_file_path = os.path.join(download_path, downloaded_file)
                # if we find an info.json, let's unzip it's associated zip
                if downloaded_file == "info.json":
                    # add the info to our list of info jsons
                    inner_data_file = open(downloaded_file_path, 'r')
                    inner_info_json = json.load(inner_data_file)
                    info_jsons.append(inner_info_json)

                    # if this bundle is an asset
                    if inner_info_json["type"] == "asset":
                        # let's extract the asset zip to the vendor path
                        downloaded_asset_path = os.path.join(download_path, inner_info_json["name"] + ".zip")  # need to change bundlename to name for fk testing TODO add something to folder name if version is static
                        print("Unzipping " + inner_info_json["bundlename"] + "!")

                        downloaded_asset_file = zipfile.ZipFile(downloaded_asset_path)

                        bundle_vendor_path = os.path.join(vendor_path, inner_info_json["bundlename"])

                        if not os.path.exists(bundle_vendor_path):
                            os.makedirs(bundle_vendor_path)
                        downloaded_asset_file.extractall(bundle_vendor_path)

                        # after extracting zip, let's delete
                        downloaded_asset_file.close()
                        os.remove(downloaded_asset_path)

def check_if_installed(bundlename, path, requested_version):
    # if no version specified, assume latest
    if requested_version is None:
        try:
            requested_version = requests.get("http://trimm3d.com/latest/" + bundlename).json()["latest-version"]
        except ValueError or KeyError:
            print("---NOTICE---")
            print("Bundle '" + bundlename + "' does not exist on the Trimm server!")
            exit()

    if path is None:
        path = set_path(path)

    bundle = bundlename.split("/")
    bundle_path = os.path.join(path, bundle[0])
    bundle_path = os.path.join(bundle_path, bundle[1])

    if not os.path.isdir(bundle_path):
        return False

    trimm_path = os.path.join(path, "trimm.json")
    trimm_json = {"assets": {}, "packages": {}}
    if os.path.isfile(trimm_path):
        data_file = open(trimm_path, 'r')
        trimm_json = json.load(data_file)
    trimm_assets = trimm_json["assets"]
    trimm_packages = trimm_json["packages"]

    version = None

    if bundlename in trimm_assets:
        version = trimm_assets[bundlename]
    elif bundlename in trimm_packages:
        version = trimm_packages[bundlename]

    if version is not None:
        if version == requested_version:
            print("Requested version of " + bundlename + " is already installed! Skipping...")
            return True

        print("Version " + version + " of the bundle named " + bundlename
              + " already exists! Skipping download.")
        return True

    return False


def set_path(path):
    path = path + "Assets/vendor/"
    return path


def create_git_ignore(path):
    gitignore_filepath = os.path.join(path, ".gitignore")
    if not os.path.isfile(gitignore_filepath):
        gitignore = open(gitignore_filepath, "w+")
        gitignore.write("*\n")
        gitignore.write("!*/\n")
        gitignore.write("!.gitignore\n")
        gitignore.write("!*.meta\n")
        gitignore.write("!trimm.json\n")
        gitignore.close()
