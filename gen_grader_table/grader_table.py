import tomlkit
import os
import datetime
import logging

from tomlkit import document, table, comment, dumps
from canvas_lms_api import get_client, Group, Person

from pathlib import Path

import mucs_database.store_objects as dao
logger = logging.getLogger(__name__)

class Config:
    def __init__(self, canvas_token: str, course_id: int):
        self.canvas_token = canvas_token
        self.course_id = course_id



def validate_cache(grader_name: str, roster_invalidation_days: int = 14,) -> bool:
    """
    Checks if the last time the database was updated with roster data is within an acceptable range.
    Returns false if the cache is invalid. 
    :param grader_name: The name of the grader
    :param roster_invalidation_days: How many days can pass before a new update is needed
    """
    invalidation_date = datetime.datetime.now() - datetime.timedelta(days=roster_invalidation_days)
    logger.debug(f"Checking last write. Invalidation date: {invalidation_date}")
    logger.debug(f"Invalidation days: {roster_invalidation_days}")
    # First, we can determine the last time all grading groups were updated.
    last_write_date = dao.get_cache_date_from_mucs_course("last_grader_pull")
    if last_write_date is None:
        logger.info("Refreshing grading group data")
        return False
    
    # Let's check the last time the grader was updated.
    grader_dict = dao.get_grader_by_name(grader_name)
    if grader_dict is None:
        logger.info(f"Refreshing {grader_name}'s grading group")
    last_write_date = datetime.datetime.fromtimestamp(grader_dict["last_updated"])
    if last_write_date > invalidation_date:
        logger.info(f"Grading group data for {grader_name} is recent enough to be reliably used.")
        return True
    return False
def generate_grader_roster(course_id: int, group: Group = None, grader_name: str = None, roster_invalidation_days: int = 14):
    if validate_cache(roster_invalidation_days=roster_invalidation_days, grader_name=grader_name):
        logger.info(f"There is no need to regenerate the grader roster based on roster invalidation days = {roster_invalidation_days}")
        return 
    logger.info(f"Preparing roster data for {group.name if group is not None else grader_name}")
    # we need to find the group ID corresponding to the invoked grader
    if group is None:
        group = find_grader_group(grader_name=grader_name, course_id=course_id)
    if group is None:
        logger.warning(f"A group corresponding to {group.name if group is not None else grader_name} was not found in the Canvas course {str(course_id)}")
    # place it in DB
    grading_group_id = dao.store_grading_group(id=group.id, name=group.name, course_id=course_id, replace=True)
    # now we can retrieve a list of the users in the grader's group
    users = get_client._groups.get_people_from_group(group_id=group.id, per_page=50)

    for user in users:
        dao.store_student(pawprint=user.login_id, name=user.name, sortable_name=user.sortable_name, canvas_id=user.id, grader_id=grading_group_id, replace=True)

def find_grader_group(grader_name: str, course_id: int,) -> Group:
    groups = get_client._groups.get_groups_from_course(course_id=course_id)
    for group in groups:
        if grader_name == group.name:
            return group

def generate_all_rosters(course_id: int):
    groups = get_client._groups.get_groups_from_course(course_id=course_id)
    for group in groups:
        generate_grader_roster(group=group, course_id=group.id, grader_name=group.name)


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