import os
import shutil
import time
from pathlib import Path

import luigi

# from luigi.mock import MockFileSystem

class DownloadiCloud(luigi.Task):
    file_path = luigi.Parameter()
    def run(self):
        os.system(f"brctl download {self.file_path}")
    def output(self):
        return luigi.LocalTarget(self.file_path)


class MoveImageToOutputFolder(luigi.Task):
    file_path = luigi.Parameter()
    output_path = luigi.Parameter()
    def requires(self):
        return DownloadiCloud(file_path=self.file_path)

    def output(self):
        output = luigi.LocalTarget(self.output_path)
        target = self.input()
        if not output.exists():
            target.move(self.output_path)
        return output



class GetCameraTags(luigi.Task):
    file_path = luigi.Parameter()
    output_path = luigi.Parameter()
    output_txt_path = luigi.Parameter()

    def requires(self):
        return MoveImageToOutputFolder(file_path=self.file_path, output_path=self.output_path)

    def run(self):
        file_contents = ""
        if self.output().exists():
            with self.output().open("r") as txt_file:
                file_contents = txt_file.read()
        with self.output().open("w") as txt_file:
            txt_file.write(file_contents)
            txt_file.write("Camera Tags: \n")

    def output(self):
        return luigi.LocalTarget(self.output_txt_path)

class GetLensTags(luigi.Task):
    file_path = luigi.Parameter()
    output_path = luigi.Parameter()
    output_txt_path = luigi.Parameter()

    def requires(self):
        return MoveImageToOutputFolder(file_path=self.file_path, output_path=self.output_path)

    def run(self):
        file_contents = ""
        if self.output().exists():
            with self.output().open("r") as txt_file:
                file_contents = txt_file.read()
        with self.output().open("w") as txt_file:
            txt_file.write(file_contents)
            txt_file.write("Lens Tags: \n")

    def output(self):
        return luigi.LocalTarget(self.output_txt_path)

class AddPersonalTags(luigi.Task):
    file_path = luigi.Parameter()
    output_path = luigi.Parameter()
    output_txt_path = luigi.Parameter()

    def requires(self):
        return MoveImageToOutputFolder(file_path=self.file_path, output_path=self.output_path)

    def run(self):
        file_contents = ""
        if self.output().exists():
            with self.output().open("r") as txt_file:
                file_contents = txt_file.read()
        with self.output().open("w") as txt_file:
            txt_file.write(file_contents)
            txt_file.write("Photographer Tags: \n")

    def output(self):
        return luigi.LocalTarget(self.output_txt_path)

class ProcessImage(luigi.Task):
    file_path = luigi.Parameter()
    output_path = luigi.Parameter(default="nowhere")
    output_txt_path = luigi.Parameter(default="nowhere")
    def requires(self):
        image_path = Path(self.file_path)
        image_dir = image_path.parent
        output_dir = image_dir / "tagged"
        self.output_path = output_dir / image_path.name
        self.output_txt_path = (image_dir / "tagged" / image_path.stem).with_suffix(".txt")
        yield MoveImageToOutputFolder(file_path=self.file_path, output_path=self.output_path)
        tags_kwargs = {
            "file_path": self.file_path,
            "output_path": self.output_path,
            "output_txt_path": self.output_txt_path
        }
        yield GetCameraTags(**tags_kwargs)
        yield GetLensTags(**tags_kwargs)
        yield AddPersonalTags(**tags_kwargs)

    def run(self):
        file_contents = ""
        if self.output().exists():
            with self.output().open("r") as txt_file:
                file_contents = txt_file.read()

        with self.output().open("w") as txt_file:
            txt_file.write(file_contents)
            txt_file.write("Tags Generated\n")

    def output(self):
        return luigi.LocalTarget(self.output_txt_path)
