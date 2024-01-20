import math
import os
import shutil
import time
from datetime import date
from pathlib import Path
from uuid import uuid4

import luigi
import piexif

from .data.cameras import CAMERAS
from .data.lenses import LENSES


def get_exif_data(file_path):
    exif_data = {}
    exif_dict = piexif.load(file_path)
    for ifd in ("0th", "Exif", "GPS", "1st"):
        for tag in exif_dict[ifd]:
            if type(exif_dict[ifd][tag]) == bytes:
                exif_data[piexif.TAGS[ifd][tag]["name"]] = exif_dict[ifd][tag].decode("utf-8")
            else:
                exif_data[piexif.TAGS[ifd][tag]["name"]] = exif_dict[ifd][tag]
    return exif_data


def convert_tags_to_hashtags(raw_tags):
    if "NotFound" not in raw_tags:
        hashtags = [f"#{tag}" for tag in raw_tags]
        hashtag_text = " ".join(hashtags)
        return hashtag_text
    return raw_tags


class DownloadiCloud(luigi.Task):
    file_path = luigi.Parameter()
    uuid = luigi.Parameter()
    def run(self):
        os.system(f"brctl download {self.file_path}")
    def output(self):
        return luigi.LocalTarget(self.file_path)


class AddImageName(luigi.Task):
    file_path = luigi.Parameter()
    output_path = luigi.Parameter()
    output_txt_path = luigi.Parameter()
    uuid = luigi.Parameter()
    def run(self):
        file_contents = ""
        image_path = Path(self.file_path)
        if self.output().exists():
            with self.output().open("r") as txt_file:
                file_contents = txt_file.read()
        with self.output().open("w") as txt_file:
            txt_file.write(file_contents)
            txt_file.write(f"\nImage Name: {image_path.stem}\n")

    def output(self):
        return luigi.LocalTarget(self.output_txt_path)


class MoveImageToOutputFolder(luigi.Task):
    file_path = luigi.Parameter()
    output_path = luigi.Parameter()
    uuid = luigi.Parameter()
    def requires(self):
        yield DownloadiCloud(file_path=self.file_path, uuid=self.uuid)

    def output(self):
        output = luigi.LocalTarget(self.output_path)
        target = self.input()[0]
        if not output.exists():
            target.move(self.output_path)
        return output



class GetCameraTags(luigi.Task):
    file_path = luigi.Parameter()
    output_path = luigi.Parameter()
    output_txt_path = luigi.Parameter()
    uuid = luigi.Parameter()

    def requires(self):
        yield MoveImageToOutputFolder(file_path=self.file_path, output_path=self.output_path, uuid=self.uuid)
        yield AddImageName(file_path=self.file_path, output_path=self.output_path, output_txt_path=self.output_txt_path, uuid=self.uuid)

    def get_camera_model_tags(self, image_data):
        model_tags = []
        if "Model" in image_data:
            try:
                model_data = CAMERAS[image_data["Model"]]
                for section, tags in model_data.items():
                    model_tags.extend(tags)
            except KeyError:
                model_tags.append(f"CameraNotFound - [{image_data["Model"]}]")
        return model_tags

    def get_exposure_tags(self, image_data):
        exposure_tags = []
        if "ExposureTime" in image_data:
            n_e, d_e = image_data["ExposureTime"]
            exposure_time = n_e / d_e
            if exposure_time >= 1:
                exposure_value = str(exposure_time).replace(".", "point")
                exposure_tag = f"{exposure_value}s"
                exposure_tags.append("longexposure")
            else:
                exposure_value = int(1/exposure_time)
                exposure_tag = f"1_{exposure_value}s"
            exposure_tags.append(exposure_tag)
        return exposure_tags

    def run(self):
        image_data = get_exif_data(str(self.output_path))
        camera_tags = []
        camera_tags += self.get_exposure_tags(image_data)
        camera_tags += self.get_camera_model_tags(image_data)
        camera_hashtags = convert_tags_to_hashtags(camera_tags)
        file_contents = ""

        if self.output().exists():
            with self.output().open("r") as txt_file:
                file_contents = txt_file.read()
        with self.output().open("w") as txt_file:
            txt_file.write(file_contents)
            txt_file.write(f"Camera Tags: {camera_hashtags}\n")

    def output(self):
        return luigi.LocalTarget(self.output_txt_path)


class GetLensTags(luigi.Task):
    file_path = luigi.Parameter()
    output_path = luigi.Parameter()
    output_txt_path = luigi.Parameter()
    uuid = luigi.Parameter()

    def get_aperture_tags(self, image_data):
        aperture_tags = []
        if "FNumber" in image_data:
            n_f, d_f = image_data["FNumber"]
            f_number = n_f / d_f
            if d_f != 1:
                aperture_tag = f"F{f_number}".replace(".","_")
            else:
                aperture_tag = f"F{n_f}"
            aperture_tags.append(aperture_tag)
        return aperture_tags

    def get_focal_length_tags(self, image_data):
        focal_length_tags = []
        if "FocalLength" in image_data:
            n_l, d_f = image_data["FocalLength"]
            focal_length = n_l / d_f
            actual_focal_length = f"{focal_length}mm".replace(".0", "").replace(".","_")
            focal_length_tags.append(actual_focal_length)
            # if hasattr(image_data, "focal_length_in_35mm_film"):
            #     equivalent_focal_length = f"{int(image_data.focal_length_in_35mm_film)}mm".replace(".0", "").replace(".","_")
            #     focal_length_tags.append(equivalent_focal_length)
        return focal_length_tags

    def get_lens_model_data(self, image_data):
        lens_model_tags = []
        if "LensModel" in image_data:
            try:
                model_data = LENSES[image_data["LensModel"]]
                for section, tags in model_data.items():
                    lens_model_tags.extend(tags)
            except KeyError:
                lens_model_tags.append(f"LensNotFound - [{image_data["LensModel"]}]")
        return lens_model_tags

    def requires(self):
        yield MoveImageToOutputFolder(file_path=self.file_path, output_path=self.output_path, uuid=self.uuid)
        yield AddImageName(file_path=self.file_path, output_path=self.output_path, output_txt_path=self.output_txt_path, uuid=self.uuid)

    def run(self):
        image_data = get_exif_data(str(self.output_path))
        lens_tags = []
        lens_tags += self.get_aperture_tags(image_data)
        lens_tags += self.get_focal_length_tags(image_data)
        lens_tags += self.get_lens_model_data(image_data)
        lens_hashtags = convert_tags_to_hashtags(lens_tags)
        file_contents = ""
        if self.output().exists():
            with self.output().open("r") as txt_file:
                file_contents = txt_file.read()
        with self.output().open("w") as txt_file:
            txt_file.write(file_contents)
            txt_file.write(f"Lens Tags: {lens_hashtags}\n")

    def output(self):
        return luigi.LocalTarget(self.output_txt_path)


class AddPersonalTags(luigi.Task):
    file_path = luigi.Parameter()
    output_path = luigi.Parameter()
    output_txt_path = luigi.Parameter()
    uuid = luigi.Parameter()

    def requires(self):
        yield MoveImageToOutputFolder(file_path=self.file_path, output_path=self.output_path, uuid=self.uuid)
        yield AddImageName(file_path=self.file_path, output_path=self.output_path, output_txt_path=self.output_txt_path, uuid=self.uuid)

    def run(self):
        personal_tags = [
            "disabledphotographer",
            "FibroPhotographer",
            "SpoonyPhotography"

        ]
        personal_hashtags = convert_tags_to_hashtags(personal_tags)

        file_contents = ""
        if self.output().exists():
            with self.output().open("r") as txt_file:
                file_contents = txt_file.read()
        with self.output().open("w") as txt_file:
            txt_file.write(file_contents)
            txt_file.write(f"Photographer Tags: {personal_hashtags}\n")

    def output(self):
        return luigi.LocalTarget(self.output_txt_path)

IMAGE_TYPES = ["jpg", "jpeg", "heic"]


class ProcessImage(luigi.Task):
    file_path = luigi.Parameter()
    output_path = luigi.Parameter(default="nowhere")
    output_txt_path = luigi.Parameter(default="nowhere")
    def requires(self):
        path_components = self.file_path.lower().split(".")
        if path_components[-1] in IMAGE_TYPES:        
            image_path = Path(self.file_path)
            image_dir = image_path.parent
            output_dir = image_dir / "tagged"
            self.output_path = output_dir / image_path.name
            self.output_txt_path = (image_dir / "tagged" / image_path.stem).with_suffix(".txt")
            # today_str = date.today().strftime("%d-%m-%Y")
            # self.output_txt_path = (image_dir / "tagged" / today_str).with_suffix(".txt")
            random_uuid = str(uuid4())
            tags_kwargs = {
                "file_path": self.file_path,
                "output_path": self.output_path,
                "output_txt_path": self.output_txt_path,
                "uuid": random_uuid,
            }

            yield GetCameraTags(**tags_kwargs)
            yield GetLensTags(**tags_kwargs)
            yield AddPersonalTags(**tags_kwargs)

    def run(self):
        path_components = self.file_path.lower().split(".")
        if path_components[-1] in IMAGE_TYPES:
            file_contents = ""
            if self.output().exists():
                with self.output().open("r") as txt_file:
                    file_contents = txt_file.read()
            raw_lines = file_contents.split("\n")
            tags = [raw_line.split(": ")[1] for raw_line in raw_lines if ": " in raw_line]
            all_tags = " ".join(tags)
            with self.output().open("w") as txt_file:
                txt_file.write(file_contents)
                txt_file.write(f"Tags Generated: {all_tags}\n")

    def output(self):
        return luigi.LocalTarget(self.output_txt_path)
