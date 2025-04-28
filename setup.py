from setuptools import setup, find_packages

setup(
  name="gen_grader_table",
  version="0.2",
  packages=find_packages(include=["gen_grader_table", "gen_grader_table.*"]),
    install_requires=[
        "canvas_lms_api",
    ],
)