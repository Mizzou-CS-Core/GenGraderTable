import datetime
import logging
from pathlib import Path

import mucs_database.store_objects as dao
from canvas_lms_api import get_client, Group
from tomlkit import document, table, comment, dumps

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, canvas_token: str, course_id: int, mucsv2_instance_code: str, db_path: str, canvas_url_base: str,
                 roster_invalidation_days: int, ):
        self.mucsv2_instance_code = mucsv2_instance_code
        self.canvas_token = canvas_token
        self.course_id = course_id
        self.db_path = db_path
        self.canvas_url_base = canvas_url_base
        self.roster_invalidation_days = roster_invalidation_days


def is_cache_valid(grader_name: str, roster_invalidation_days: int = 14, ) -> bool:
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
        return False
    last_write_date = grader_dict["last_updated"]
    if last_write_date > invalidation_date:
        logger.info(f"Grading group data for {grader_name} is recent enough to be reliably used.")
        return True
    return False


def generate_grader_roster(course_id: int, group: Group = None, grader_name: str = None,
                           roster_invalidation_days: int = 14):
    if is_cache_valid(roster_invalidation_days=roster_invalidation_days, grader_name=grader_name):
        return
    logger.info(f"Preparing roster data for {group.name if group is not None else grader_name}")
    # we need to find the group ID corresponding to the invoked grader
    if group is None:
        group = find_grader_group(grader_name=grader_name, course_id=course_id)
    if group is None:
        logger.warning(
            f"A group corresponding to {group.name if group is not None else grader_name} was not found in the Canvas "
            f"course {str(course_id)}")
    # place it in DB
    grading_group_id = dao.store_grading_group(id=group.id, name=group.name, course_id=course_id, replace=True)
    # now we can retrieve a list of the users in the grader's group
    users = get_client().groups.get_people_from_group(group_id=group.id, per_page=50)

    for user in users:
        dao.store_student(pawprint=user.login_id, name=user.name, sortable_name=user.sortable_name,
                          canvas_id=user.canvas_id, grader_id=grading_group_id, replace=True)


def find_grader_group(grader_name: str, course_id: int, ) -> Group:
    groups = get_client().groups.get_groups_from_course(course_id=course_id)
    for group in groups:
        if grader_name == group.name:
            return group


def generate_all_rosters(course_id: int):
    groups = get_client().groups.get_groups_from_course(course_id=course_id)
    for group in groups:
        generate_grader_roster(group=group, course_id=course_id, grader_name=group.name)


def prepare_toml(mucsv2_instance_code: str = "", db_path: str = "", canvas_token: str = "", canvas_course_id: int = -1,
                 canvas_url_base: str = "https://umsystem.instructure.com/api/v1/", roster_invalidation_days: int = 0,
                 config_base=Path("")) -> None:
    doc = document()
    general = table()
    general.add(comment("The mucsv2 instance code of your course."))
    general.add("mucsv2_instance_code", mucsv2_instance_code)
    general.add(comment("How many days can pass before we need to explicitly regenerate roster data"))
    general.add("roster_invalidation_days", roster_invalidation_days)
    doc['general'] = general
    paths = table()
    paths.add(comment("Path to MUCSv2 Database"))
    paths.add("db_path", db_path)
    doc['paths'] = paths

    canvas = table()
    canvas.add(comment("The Canvas LMS instance to use."))
    canvas.add("canvas_url_base", canvas_url_base)
    canvas.add(comment("The Canvas LMS Token identifying your user session."))
    canvas.add("canvas_token", canvas_token)
    canvas.add(comment("The Canvas LMS course ID identifying your course."))
    canvas.add("canvas_course_id", canvas_course_id)
    doc['canvas'] = canvas

    with open(config_base / "gen_grader_table.toml", 'w') as f:
        f.write(dumps(doc))
    logger.info("Created default toml config")
