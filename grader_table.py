import tomlkit
import os
from tomlkit import document, table, comment, dumps
from CanvasRequestLibrary.main import CanvasClient

class Config:
    def __init__(self, canvas_token: str, course_id: int):
        self.canvas_token = canvas_token
        self.course_id = course_id
class Group:
    def __init__(self, name: str, id: int, members_count: int):
        self.name = name
        self.id = id
        self.members_count = members_count
    @staticmethod
    def parse_groups_from_json(groups_json) -> []:
        groups = []
        for body in groups_json:
            groups.append(Group(name=body['name'], id=body['id'], members_count=body['members_count']))
        return groups


def generate_grader_roster(course_id: int, canvas_token: str, group: Group = None, grader_name: str = None, path: str = None, roster_invalidation_days: int = 14):
    name = group.name if group is not None else grader_name
    csv_rosters_path = f"{path or os.getcwd}/csv_rosters"
    grader_csv = f"{name}.csv"
    grader_csv_path = f"{csv_rosters_path}/{grader_csv}"
    fieldnames = ['pawprint', 'canvas_id', 'name', 'date']
    # first we'll check if the roster already exists.
    if os.path.exists(grader_csv_path) and Path(grader_csv_path).stat().st_size != 0 and roster_invalidation_days > 0:
        # if it does, let's see how old it is
        # every student has a date appended to it which should be the same so we'll just check the first one
        with open(grader_csv_path, 'r', newline='') as csvfile:
            reader = DictReader(csvfile, fieldnames=fieldnames)
            next(reader)  # consume header
            sample_row = next(reader)
            stored_date_str = sample_row['date']
            stored_date_obj = datetime.datetime.strptime(stored_date_str, "%Y-%m-%d %H:%M:%S.%f")
            invalidation_date = datetime.datetime.now() - datetime.timedelta(days=roster_invalidation_days)
            if stored_date_obj > invalidation_date:
                print(f"{Fore.BLUE}Roster data for {group.name} is recent enough to be used{Style.RESET_ALL}")
                return
    print(f"{Fore.BLUE}Preparing roster data{Style.RESET_ALL}")
    # we need to find the group ID corresponding to the invoked grader
    if group is None:
        group = find_grader_group(grader_name=name, course_id=course_id, canvas_token=canvas_token)
    if group is None:
        print(f"{Fore.RED}A group corresponding to {name} was not found in the Canvas course {str(course_id)}{Style.RESET_ALL}")
    # now we can retrieve a list of the users in the grader's group
    group_api = config_obj.api_prefix + "groups/" + str(group_id) + "/users?per_page=100"
    users_in_group = make_api_call(group_api, config_obj.api_token)

    if not os.path.exists(csv_rosters_path):
        os.makedirs(csv_rosters_path)
    with open(csv_rosters_path + "/" + command_args_obj.grader_name + ".csv", 'w', newline='') as csvfile:
        writer = DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        data = []
        for key in users_in_group.json():
            roster_dict = {'pawprint': key['login_id'], 'canvas_id': key['id'], 'name': key['sortable_name'],
                    'date': datetime.datetime.now()}
            data.append(roster_dict)
        writer.writerows(data)

def find_grader_group(grader_name: str, canvas_token: str, course_id: int) -> Group:
    client = CanvasClient(token=canvas_token, url_base=url_base)
    groups = Group.parse_groups_from_json(client._groups.get_groups_from_course(course_id=course_id))
    for group in groups:
        if grader_name == group.name:
            return group
def get_group_members(group: Group, course_id: int, canvas_token: str):
    pass

def generate_all_rosters(course_id: int, canvas_token: str, path: str = None, url_base: str = "https://umsystem.instructure.com/api/v1/"):
    client = CanvasClient(token=canvas_token, url_base=url_base)
    groups = Group.parse_groups_from_json(client._groups.get_groups_from_course(course_id=course_id))
    
    pass


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



if __name__ == "__main__":
    main()