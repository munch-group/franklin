import requests
import time
import click
import subprocess
from subprocess import DEVNULL, STDOUT, PIPE
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Tuple, List, Dict, Callable, Any
import importlib_resources
from . import config as cfg
from . import utils
from . import cutie
from . import terminal as term
from .logger import logger
from .utils import is_educator
from . import system

def get_registry_listing(registry: str) -> Dict[Tuple[str, str], str]:
    """
    Fetches the listing of images in the GitLab registry.

    Parameters
    ----------
    registry : 
        URl to the GitLab registry.

    Returns
    -------
    :
        A dictionary with the course and exercise names as keys and the image locations
    """
    s = requests.Session()
    s.headers.update({'PRIVATE-TOKEN': cfg.gitlab_token})
    images = {}
    r  = s.get(registry,  headers={ "Content-Type" : "application/json"})
    if not r.ok:
      r.raise_for_status()
    for entry in r.json():
        group, course, exercise = entry['path'].split('/')
        if exercise in ['base']:
            continue
        if course in ['base-images', 'base-templates']:
            continue
        images[(course, exercise)] = entry['location']
    return images


def get_course_names() -> Dict[str, str]:
    """
    Fetches the names of the courses in the GitLab group.

    Returns
    -------
    :
        A dictionary with the course names and the Danish course names
    """
    s = requests.Session()
    s.headers.update({'PRIVATE-TOKEN': cfg.gitlab_token})
    url = f'{cfg.gitlab_api_url}/groups/{cfg.gitlab_group}/subgroups'

    name_mapping = {}
    r  = s.get(url, headers={ "Content-Type" : "application/json"})
    if not r.ok:
        r.raise_for_status()

    for entry in r.json():
        if 'template' in entry['path'].lower():
            continue
        if entry['description']:
            name_mapping[entry['path']] = entry['description']
        else:
            name_mapping[entry['path']] = entry['path']
    
    return name_mapping


def get_exercise_names(course: str) -> Dict[str, str]:
    """
    Fetches the names of the exercises in the GitLab group.

    Parameters
    ----------
    course : 
        Course name.

    Returns
    -------
    :
        A dictionary with the exercise names and the Danish exercise names
    """
    s = requests.Session()
    s.headers.update({'PRIVATE-TOKEN': cfg.gitlab_token})
    url = f'{cfg.gitlab_api_url}/groups/{cfg.gitlab_group}%2F{course}/projects'

    name_mapping = {}
    r  = s.get(url, headers={ "Content-Type" : "application/json"})
    if not r.ok:
        r.raise_for_status()

    for entry in r.json():
        if entry['description']:
            name_mapping[entry['path']] = entry['description']
        else:
            name_mapping[entry['path']] = entry['path']
    
    return name_mapping


def pick_course() -> Tuple[str, str]:
    """
    Prompts the user to select a course.

    Returns
    -------
    :
        The course name and the Danish name of the course.
    """
    course_names = get_course_names()
    course_group_names, course_danish_names,  = zip(*sorted(course_names.items()))
    term.secho("\nUse arrow keys to select course and press Enter:", fg='green')
    captions = []
    course_idx = cutie.select(course_danish_names, caption_indices=captions, selected_index=0)
    return course_group_names[course_idx], course_danish_names[course_idx]


def select_exercise(exercises_images: str) -> Tuple[str, str]:
    """
    Prompts the user to select an exercise.

    Parameters
    ----------
    exercises_images : 
        A dictionary with the exercise and exercise names as keys and the image locations

    Returns
    -------
    :
        A tuple of the course name and the exercise name.
    """
    hide_hidden = not is_educator()
    while True:
        course, danish_course_name = pick_course()
        exercise_names = get_exercise_names(course)
        # only use those with listed images and not with 'HIDDEN' in the name
        for key, val in list(exercise_names.items()):
            if (course, key) not in exercises_images:
                del exercise_names[key]
            if 'HIDDEN' in val:
                if hide_hidden:
                    del exercise_names[key]
                else:
                    exercise_names[key] = val + ' (hidden from students)'
                    
        if exercise_names:
            break
        term.secho(f"\n  >>No exercises for {danish_course_name}<<", fg='red')
        time.sleep(2)

    exercise_repo_names, listed_exercise_names = zip(*sorted(exercise_names.items()))
    term.secho(f'\nUse arrow keys to select exercise in "{danish_course_name}" and press Enter:', fg='green')
    captions = []
    exercise_idx = cutie.select(listed_exercise_names, caption_indices=captions, selected_index=0)
    exercise = exercise_repo_names[exercise_idx]

    term.secho(f"\nSelected:", fg='green')
    term.echo(f"Course: {danish_course_name}")
    term.echo(f"Exercise: {listed_exercise_names[exercise_idx]}")
    term.echo()
    time.sleep(1)

    return (course, danish_course_name), (exercise, listed_exercise_names[exercise_idx])


def select_image() -> str:
    """
    Prompts the user to select a course, then an exercise mapping to an image location.

    Returns
    -------
    :
        Image location.
    """
    registry = f'{cfg.gitlab_api_url}/groups/{cfg.gitlab_group}/registry/repositories'
    exercises_images = get_registry_listing(registry)

    (course, _), (exercise, _) = select_exercise(exercises_images)

    selected_image = exercises_images[(course, exercise)]
    return selected_image


@click.command(epilog=f'See {cfg.documentation_url} for more details')
def download():
    """Download selected exercise from GitLab
    """
    try:
        import franklin_educator
        term.boxed_text("Are you an educator?",
                        ['It seems you are an educator. If you intend upload to edit and '
                         'upload changes to an exercise, you must use "franklin git down" instead.'],
                        fg='red')
        click.confirm("Continue?", default=False, abort=True)
    except ImportError:
        pass

    # get images for available exercises
    registry = f'{cfg.gitlab_api_url}/groups/{cfg.gitlab_group}/registry/repositories'
    exercises_images = get_registry_listing(registry)

    # pick course and exercise
    (course, _), (exercise, listed_exercise_name) = select_exercise(exercises_images)
    listed_exercise_name = listed_exercise_name.replace(' ', '-')

    # url for cloning the repository
    repo_name = exercise.split('/')[-1]
    clone_url = f'https://gitlab.au.dk/{cfg.gitlab_group}/{course}/{repo_name}.git'
    repo_local_path = Path().cwd() / listed_exercise_name

    if system.system() == 'Windows':
        repo_local_path = PureWindowsPath(repo_local_path)

    if repo_local_path.exists():
        term.secho(f"The exercise folder already exists:\n{repo_local_path}.")
        raise click.Abort()

    output = utils.run_cmd(f'git clone {clone_url} {repo_local_path}')

    # Reads contents with UTF-8 encoding and returns str.
    # eml = importlib.resources.files('email.tests.data').joinpath('message.eml').read_text()
    template_files = [p.name for p in importlib_resources.files().joinpath('data/templates/exercise').iterdir()]
    dev_files = [p for p in template_files if p != 'exercise.ipynb']

    for path in dev_files:
        path = os.path.join(repo_local_path, path)
        if os.path.exists(path):
            logger.debug(f"Removing {path}")
            os.remove(path)

    term.secho(f"Downloaded exercise to folder: {repo_local_path}")
