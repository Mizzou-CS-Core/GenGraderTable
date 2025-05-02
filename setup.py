from setuptools import setup, find_packages

setup(
    name="gen_grader_table",
    version="0.2",
    packages=find_packages(include=["gen_grader_table", "gen_grader_table.*"]),
    install_requires=[
        "canvas_lms_api @ git+https://github.com/Mizzou-CS-Core/CanvasRequestLibrary.git#egg=canvas_lms_api",
        "mucs_database @ git+https://github.com/Mizzou-CS-Core/MUCSDao.git#egg=mucs_database"
    ],
)
