import tomlkit
import os
import datetime
from tomlkit import document, table, comment, dumps
from CanvasRequestLibrary import CanvasClient, Group, Person

from csv import DictReader, DictWriter
from pathlib import Path

from colorama import Fore
from colorama import Style

class Config:
    def __init__(self, canvas_token: str, course_id: int):
        self.canvas_token = canvas_token
        self.course_id = course_id


def generate_grader_roster(course_id: int, canvas_token: str, group: Group = None, grader_name: str = None, path: str = None, roster_invalidation_days: int = 14):
    csv_rosters_path = f"{path if path is not None else os.getcwd()}/csv_rosters"
    grader_csv = f"{group.name if group is not None else grader_name}.csv"
    grader_csv_path = f"{csv_rosters_path}/{grader_csv}"
    fieldnames = ['pawprint', 'canvas_id', 'name']
    # first we'll check if the roster already exists.
    if os.path.exists(grader_csv_path) and Path(grader_csv_path).stat().st_size != 0 and roster_invalidation_days > 0:
        # if it does, let's see how old it is
        file_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(grader_csv_path))
        invalidation_date = datetime.datetime.now() - datetime.timedelta(days=roster_invalidation_days)
        if file_mod_time > invalidation_date:
                print(f"{Fore.BLUE}Roster data for {group.name if group is not None else grader_name} is recent enough to be used{Style.RESET_ALL}")
                return

    print(f"{Fore.BLUE}Preparing roster data for {group.name if group is not None else grader_name}{Style.RESET_ALL}")
    # we need to find the group ID corresponding to the invoked grader
    if group is None:
        group = find_grader_group(grader_name=grader_name, course_id=course_id, canvas_token=canvas_token)
    if group is None:
        print(f"{Fore.RED}A group corresponding to {group.name if group is not None else grader_name} was not found in the Canvas course {str(course_id)}{Style.RESET_ALL}")
    # now we can retrieve a list of the users in the grader's group
    
    users = get_group_members(group=group, canvas_token=canvas_token)

    if not os.path.exists(csv_rosters_path):
        os.makedirs(csv_rosters_path)
    with open(grader_csv_path, 'w', newline='') as csvfile:
        writer = DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        data = []
        for user in users:
            roster_dict = {'pawprint': user.login_id, 'canvas_id': user.canvas_id, 'name': user.sortable_name}
            data.append(roster_dict)
        writer.writerows(data)

def find_grader_group(grader_name: str, canvas_token: str, course_id: int, url_base: str = "https://umsystem.instructure.com/api/v1/") -> Group:
    client = CanvasClient(token=canvas_token, url_base=url_base)
    groups = client._groups.get_groups_from_course(course_id=course_id)
    for group in groups:
        if grader_name == group.name:
            return group

def get_group_members(group: Group, canvas_token: str, url_base: str = "https://umsystem.instructure.com/api/v1/"):
    client = CanvasClient(token=canvas_token, url_base=url_base)
    return client._groups.get_people_from_group(group_id=group.id, per_page=50)

def generate_all_rosters(course_id: int, canvas_token: str, path: str = None, url_base: str = "https://umsystem.instructure.com/api/v1/"):
    client = CanvasClient(token=canvas_token, url_base=url_base)
    groups = client._groups.get_groups_from_course(course_id=course_id)
    for group in groups:
        generate_grader_roster(group=group, course_id=group.id, canvas_token=canvas_token, grader_name=group.name)


def prepare_toml() -> None:
    doc = document()

    canvas = table()
    canvas.add(comment("The Canvas LMS Token identifying your user session."))
    canvas.add("canvas_token", "")
    canvas.add(comment("The Canvas LMS course ID identifying your course."))
    canvas.add("canvas_course_id", 0)
    doc['canvas'] = canvas

    with open("config.toml", 'w') as f:
        f.write(dumps(doc))
    print("Created default toml config")
def load_config() -> Config:
    with open("config.toml", 'r') as f:
        content = f.read()
    doc = tomlkit.parse(content)

    # Extract values from the TOML document
    canvas = doc.get('canvas', {})
    return Config(canvas_token=canvas.get("canvas_token"), course_id=canvas.get("canvas_course_id"))
def main():
    if not os.path.exists("config.toml"):
        prepare_toml()
        exit()
    config = load_config()
    generate_all_rosters(course_id=config.course_id, canvas_token=config.canvas_token, path="")
    #generate_grader_roster(course_id=config.course_id, canvas_token=config.canvas_token,grader_name="Matthew")



if __name__ == "__main__":
    main()