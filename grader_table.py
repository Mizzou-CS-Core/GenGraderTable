import tomlkit
import os
from tomlkit import document, table, comment, dumps

class Config:
    def __init__(self, canvas_token: str, course_id: int):
        self.canvas_token = canvas_token
        self.course_id = course_id


def generate_grader_roster(context):
    config_obj = context.config_obj
    command_args_obj = context.command_args_obj
    csv_rosters_path = config_obj.hellbender_lab_dir + config_obj.class_code + "/csv_rosters"
    fieldnames = ['pawprint', 'canvas_id', 'name', 'date']
    # first we'll check if the roster already exists.
    if os.path.exists(csv_rosters_path + "/" + command_args_obj.grader_name + ".csv") and Path(
            csv_rosters_path + "/" + command_args_obj.grader_name + ".csv").stat().st_size != 0 and config_obj.roster_invalidation_days > 0:
        # if it does, let's see how old it is
        # every student has a date appended to it which should be the same so we'll just check the first one
        with open(csv_rosters_path + "/" + command_args_obj.grader_name + ".csv", 'r', newline='') as csvfile:
            reader = DictReader(csvfile, fieldnames=fieldnames)
            next(reader)  # consume header
            sample_row = next(reader)
            stored_date_str = sample_row['date']
            stored_date_obj = datetime.datetime.strptime(stored_date_str, "%Y-%m-%d %H:%M:%S.%f")
            invalidation_date = datetime.datetime.now() - datetime.timedelta(days=config_obj.roster_invalidation_days)
            if stored_date_obj > invalidation_date:
                print(f"{Fore.BLUE}Roster data is recent enough to be used{Style.RESET_ALL}")
                return
    print(f"{Fore.BLUE}Preparing roster data{Style.RESET_ALL}")
    # firstly, get a list of groups
    group_api = config_obj.api_prefix + "courses/" + str(config_obj.course_id) + "/groups"
    groups = make_api_call(group_api, config_obj.api_token)
    # we need to find the group ID corresponding to the invoked grader
    group_id = -1
    for key in groups.json():
        if key['name'] == command_args_obj.grader_name:
            group_id = key['id']
            # if it's still -1, we didn't find it. program will probably crash at some point but we're not going to exit because maybe a cached copy exists?
    if group_id == -1:
        print(
            f"{Fore.RED}A group corresponding to {command_args_obj.grader_name} was not found in the Canvas course {str(config_obj.course_id)}{Style.RESET_ALL}")
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

def generate_all_rosters(course_id: int, canvas_token: str):
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
    return Config(canvas_token==canvas.get("canvas_token"), course_id=canvas.get("canvas_course_id"))
def main():
    if not os.path.exists("config.toml"):
        prepare_toml()
        exit()
    config = load_config()



if __name__ == "__main__":
    main()