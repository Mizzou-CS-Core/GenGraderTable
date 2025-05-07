# gen_grader_table


This project is a set of wrappers and abstractions for adding Canvas grading groups and the associated students to a MUCSv2 course instance. 

The library has some flexibility in the way it is used, allowing for both individual group searches and insertions as well as entire courses. A cache check is also available to reduce unnecessary querying. 


It is available as both a standalone application, and as an editable pip module in use in other projects. 

It is dependent on [canvas_lms_api](https://github.com/Mizzou-CS-Core/CanvasRequestLibrary) and [mucs_database](https://github.com/Mizzou-CS-Core/MUCSDao).

Other projects in the MUCSv2 family of applications use this library, including [MUCS_Startup](https://github.com/Mizzou-CS-Core/MUCS_Startup).


## Set Up for Standalone Application

*Many of these set up steps are performed automatically if you have initialized your MUCSv2 course instance correctly using https://github.com/Mizzou-CS-Core/MUCS_Startup*. 

A Python 3.7+ interpreter is required. It is recommended that you create a Python virtual environment for using this application.
There are some required modules in MUCSMake. You can install them with `pip install -r requirements.txt`. 

To configure runtime properties, first run the program at least once. This will create an editable `config.toml` document that you can edit with your specifications. You will need to specify a database file path and the MUCSv2 instance code associated with your MUCSv2 instance. You will also need to provide your Canvas information, including a `canvas_token`, `canvas_url_base`, and the `canvas_course_id` you want to search from. 

You can also specify `roster_invalidation_days` to use the caching feature. You can set this value to anything below 1 to always regenerate data when called. 

## Set Up as Pip Library

For best results, you should use `piptools`. Add the GitHub Repo as an HTTPS URL along with `#egg-info=gen_grader_table` to a `requirements.in`. Then compile it using `pip-compile requirements.in`. This will generate a `requirements.txt` with the appropriate URL for downloading. 

## Usage

The standalone application can be run as `python3 main.py`. 




