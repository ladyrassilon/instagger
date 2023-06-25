import argparse
import datetime
import mimetypes
import os
import random
import shutil
import sys
# import requests
# import dropbox
import time
import uuid

import dateutil
import exif
import PIL


def get_aperture_tags(image_data):
    aperture_tags = []
    if hasattr(image_data, "f_number"):
        f_number = image_data.f_number
        if f_number != int(f_number):
            above, below = str(f_number).split(".")
            aperture_tag = f"F{above}_{below}"
        else:
            aperture = int(f_number)
            aperture_tag = f"F{aperture}"
        aperture_tags.append(aperture_tag)
    return aperture_tags

def get_focal_length_tags(image_data):
    focal_length_tags = []
    if hasattr(image_data, "focal_length"):
        actual_focal_length = f"{image_data.focal_length}mm".replace(".0", "").replace(".","_")
        focal_length_tags.append(actual_focal_length)
        if hasattr(image_data, "focal_length_in_35mm_film"):
            equivalent_focal_length = f"{int(image_data.focal_length_in_35mm_film)}mm".replace(".0", "").replace(".","_")
            focal_length_tags.append(equivalent_focal_length)
    return focal_length_tags

def get_camera_tags(image_data):
    if hasattr(image_data, "model"):
        camera_tag_map = {
            "ILCE-7S": ["sony", "a7s", "sonya7s", "fullframe", "emount", "femount"],
            "DSC-RX100": ["sony", "rx100", "sonyrx100", "rx100sony", "compact", "1inchsensor"],
            "ILCE-6000": ["sonya6000", "a6000photography", "a6000sony", "sony", "a6000", "mirrorless", "emount"],
            "ILCE-6400": ["sonya6400", "a6400photography", "a6400sony", "sony", "a6400", "mirrorless", "emount"],
            "iPhone XS": ["iphone", "iphonexs", "iphonephotography", "shotoniphone", "iphoneori", "smartphone", "smartphonephotography", "ios"],
            "DSC-RX100M7": ["sony", "rx1007", "sonyrx1007", "rx1007sony", "compact", "1inchsensor"],
        }
        camera_tags = camera_tag_map[image_data.model]
        return camera_tags
    return []

def get_lens_tags(image_data):
    if image_data.get("model") in ["ILCE-7S"]:
        lens_tag_map = {
            "FE 50mm F1.8": ["portraitlens", "sonylens", "primelens", "50mmprime", "50mmlens"],
            "SAMYANG AF 75mm F1.8": ["samyang", "primelens", "portraitlens", "primezoom", "75mmlens"],
            "100-400mm F5-6.3 DG DN OS | Contemporary 020": ["sigma", "sigmalens", "telephoto", "zoomlens", "variableaperture"],
            "E 24mm F2.8 F051": ["tamron", "tamronlens", "primelens", "walkaroundlens", "macrolens",],
            "E 28-75mm F2.8-2.8": ["tamron", "tamronlens", "fixedaperture", "standardlens", "zoomlens", "tamron2875"],
        }
        lens_tags = lens_tag_map[image_data.lens_model]
        return lens_tags
    elif hasattr(image_data, "lens_model"):
        lens_tag_map = {
            "SAMYANG AF 75mm F1.8": ["samyang", "primelens", "portraitlens", "primezoom", "FullFrameLens", "35mmOnCropped", "75mmlens"],
            "100-400mm F5-6.3 DG DN OS | Contemporary 020": ["sigma", "sigmalens", "telephoto", "zoomlens", "variableaperture", "35mmOnCropped"],
            "E 24mm F2.8 F051": ["tamron", "tamronlens", "primelens", "walkaroundlens", "macrolens", "35mmOnCropped", "FullFrameLens"],
            "28-100mm F1.8-4.9": ["integratedlens", "28100mm", "variableaperture", "zeisslens", "compactlens"],
            "E 55-210mm F4.5-6.3 OSS": ["telephoto", "sonylens", "zoomlens", "55210mm", "variableaperture", "OSS"],
            "E PZ 18-105mm F4 G OSS": ["telephoto", "sonylens", "zoomlens", "18105mm", "18_105mm", "fixedaperture", "OSS"],
            "----": ["wideanglelens", "wideangle", "ultrawide", "wideanglephotography", "noautofocus", "wideanglephoto", "samyang", "samyang12mm", "12mm", "rokinon", "rokinon12mm", "manualfocus", "samyanglens", "rokinonlens"],
            "E 50mm F1.8 OSS": ["portraitlens", "sonylens", "primelens", "OSS", "50mmprime", "50mmlens"],
            "30mm F1.4 DC DN | Contemporary 016": ["sigmalens", "primelens", "30mmprime", "sigmacontemporary", "fixedaperture", "standardlens"],
            "E 16mm F2.8": ["sonylens", "primelens", "16mmprime", "16mmlens", "pancakelens", "wideangle", "wideanglelens", "wideanglephoto", "wideanglephotography"],
            "E PZ 16-50mm F3.5-5.6 OSS": ["sonylens", "kitlens", "shortzoom", "zoomlens", "variableaperture", "1650mm", "16_50mm"],
            "iPhone XS front camera 2.87mm f/2.2": ["selfielens", "frontfacing", "frontfacingcamera"],
            "iPhone XS back dual camera 6mm f/2.4": ["iphone", "iphone2x", "iphonezoom", "iphone"],
            "iPhone XS back dual camera 4.25mm f/1.8": ["iphonexs", "iphone1x", "iphonewideangle", "iphonenormal"],
            "iPhone XS front TrueDepth camera 2.87mm f/2.2": ["selfielens", "portraitmode", "frontfacing", "frontfacingcamera"],
            "16mm F1.4 DC DN | Contemporary 017": ["sigmalens", "primelens", "30mmprime", "sigmacontemporary", "fixedaperture", "wideanglelens"],
            "24-200mm F2.8-4.5": ["integratedlens", "24200mm", "variableaperture", "zeisslens", "compactlens"],
            "E 28-75mm F2.8-2.8": ["tamron", "tamronlens", "fixedaperture", "standardlens", "zoomlens", "tamron2875", "35mmOnCropped", "FullFrameLens"],
        }
        lens_tag_map["Sony E PZ 18-105mm F4.0 OSS"] = lens_tag_map["E PZ 18-105mm F4 G OSS"]
        lens_tags = lens_tag_map[image_data.lens_model]
        return lens_tags
    return []

def get_exposure_tags(image_data):
    exposure_tags = []
    if hasattr(image_data, "exposure_time"):
        if image_data.exposure_time >= 1:
            exposure_value = str(image_data.exposure_time).replace(".", "point")
            exposure_tag = f"{exposure_value}s"
        else:
            exposure_value = int(1/image_data.exposure_time)
            exposure_tag = f"1_{exposure_value}s"
        exposure_tags.append(exposure_tag)
    return exposure_tags

def get_tags(image_data, image_filename):
    tags = []
    errors = []
    try:
        tags.extend(get_aperture_tags(image_data=image_data))
    except KeyError as aperture_exception:
        errors.append(f"Aperture Exception - {image_filename},{aperture_exception}")
    
    try:
        tags.extend(get_focal_length_tags(image_data=image_data))
    except KeyError as focal_length_exception:
        errors.append(f"Focal Length Exception - {image_filename},{focal_length_exception}")

    try:
        tags.extend(get_camera_tags(image_data=image_data))
    except KeyError as camera_tags_exception:
        errors.append(f"Camera Tags Exception - {image_filename},{camera_tags_exception}")

    try:
        tags.extend(get_lens_tags(image_data=image_data))
    except KeyError as lens_tags_exception:
        errors.append(f"Lens Tags Exception - {image_filename},{lens_tags_exception}")
    except KeyError as lens_tags_exception:
        errors.append(f"Lens Tags Exception - {image_filename},{lens_tags_exception}")

    try:
        tags.extend(get_exposure_tags(image_data=image_data))
    except KeyError as exposure_tags_exception:
        errors.append(f"Exposure Tags Exception - {image_filename},{exposure_tags_exception}")
    return list(set(tags)), errors

if __name__ == "__main__":
    potential_image_path = sys.argv[1]
    # mime_type = mimetypes.read_mime_types('potential_image_path')[0]
    # print(f"Mimetype = {mime_type}")
    # if potential_image_path.lower().endswith(".jpeg") or potential_image_path.lower().endswith(".jpg"):
    jpeg_path = potential_image_path
    image_path, image_filename = os.path.split(jpeg_path)
    if image_filename.lower().endswith(".icloud"):
        print(f"iCloud file {image_filename}")
        os.system(f"touch {potential_image_path}")
        print(f"Touched the file")
    elif image_filename != "tag_logging.txt":
        with open(jpeg_path, "rb") as image_file:
            image_data = exif.Image(image_file)
        raw_tags, errors = get_tags(image_data, image_filename)
        hashtags = [f"#{tag}" for tag in raw_tags]
        text = " ".join(hashtags)
        output_path = os.path.join(image_path, "tagged")
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        tag_file_path = os.path.join(output_path, "tag_file.txt")
        with open(tag_file_path, "a+") as tag_file:
            tag_file.write(f"{image_filename} - {text}")
            if errors:
                for error in errors:
                    tag_file.write(f" {error} ")
            else:
                tag_file.write("\n")    
            tag_file.write("\n")
        output_path = os.path.join(output_path, image_filename)
        print(f"{jpeg_path} {text}")
        shutil.copy2(jpeg_path, output_path)
        os.remove(jpeg_path)
