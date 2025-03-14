import requests
from .config import GITLAB_API_URL, GITLAB_GROUP, GITLAB_TOKEN
from . import utils
from . import cutie
import time
import click
from .utils import crash_report
import subprocess
import os

# curl --header "PRIVATE-TOKEN: <myprivatetoken>" -X POST "https://gitlab.com/api/v4/projects?name=myexpectedrepo&namespace_id=38"


# # this will show the namespace details of the Group with ID 54
# curl --header "PRIVATE-TOKEN: ${TOKEN}" "https://gitlab.com/api/v4/namespaces/54

# # this will show the namespace details of the User with username my-username
# curl --header "PRIVATE-TOKEN: ${TOKEN}" "https://gitlab.com/api/v4/namespace/my-username

def get_registry_listing(registry):
    s = requests.Session()
    # s.auth = ('user', 'pass')
    s.headers.update({'PRIVATE-TOKEN': GITLAB_TOKEN})
    # s.headers.update({'PRIVATE-TOKEN': 'glpat-BmHo-Fh5R\_TvsTHqojzz'})
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
        # images[(course, exercise)] = entry#['location']
    return images


def get_course_names():
    s = requests.Session()
    s.headers.update({'PRIVATE-TOKEN': GITLAB_TOKEN})
    url = f'{GITLAB_API_URL}/groups/{GITLAB_GROUP}/subgroups'
#https://gitlab.au.dk/api/v4/groups/mbg-exercises/subgroups

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


def get_exercise_names(course):
    s = requests.Session()
    s.headers.update({'PRIVATE-TOKEN': GITLAB_TOKEN})
    url = f'{GITLAB_API_URL}/groups/{GITLAB_GROUP}%2F{course}/projects'

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


def pick_course():
    course_names = get_course_names()
    course_group_names, course_danish_names,  = zip(*sorted(course_names.items()))
    utils.secho("\nUse arrow keys to select course and press Enter:", fg='green')
    captions = []
    course_idx = cutie.select(course_danish_names, caption_indices=captions, selected_index=0)
    return course_group_names[course_idx], course_danish_names[course_idx]


def select_exercise(exercises_images):
    while True:
        course, danish_course_name = pick_course()
        exercise_names = get_exercise_names(course)
        # only use those with listed images
        for key in list(exercise_names.keys()):
            if (course, key) not in exercises_images:
                del exercise_names[key]
        if exercise_names:
            break
        utils.secho(f"\n  >>No exercises for {danish_course_name}<<", fg='red')
        time.sleep(2)

    exercise_repo_names, exercise_danish_names = zip(*sorted(exercise_names.items()))
    utils.secho(f'\nUse arrow keys to select exercise in "{danish_course_name}" and press Enter:', fg='green')
    captions = []
    exercise_idx = cutie.select(exercise_danish_names, caption_indices=captions, selected_index=0)
    exercise = exercise_repo_names[exercise_idx]

    utils.secho(f"\nSelected:", fg='green')
    utils.echo(f"Course: {danish_course_name}")
    utils.echo(f"Exercise: {exercise_danish_names[exercise_idx]}")
    utils.echo()
    time.sleep(1)

    return course, exercise


def select_image():

    registry = f'{GITLAB_API_URL}/groups/{GITLAB_GROUP}/registry/repositories'
    exercises_images = get_registry_listing(registry)

    course, exercise = select_exercise(exercises_images)

    selected_image = exercises_images[(course, exercise)]
    return selected_image



@click.group(cls=utils.AliasedGroup)
def gitlab():
    """GitLab commands."""
    pass


def _gitlab_download():


    utils.boxed_text("Convenience upload", [
        'This command executes the following git commands:',
        '',
        '  git add -u',
        '  git commit -m "update"',
        '  git push',
        '',
        'It only works if no other changes have been made to the remote repository since you "downloaded" it',
        ])


    click.confirm('Do you want to continue?', abort=True)



    registry = f'{GITLAB_API_URL}/groups/{GITLAB_GROUP}/registry/repositories'
    exercises_images = get_registry_listing(registry)

    course, exercise = select_exercise(exercises_images)


    output = subprocess.check_output(utils._cmd(f'git clone git@gitlab.au.dk:{GITLAB_GROUP}/{course}/{exercise}.git')).decode()
    print(output)
    #_command(f'git clone {exercise}', silent=True)

@gitlab.command('download')
@crash_report
def gitlab_download():
    '''"Download" exercise from GitLab'''
    _gitlab_download()


def _gitlab_upload():

    utils.boxed_text("Convenience download", [
        'This command executes the following git commands:',
        '',
        '  git add -u',
        '  git commit -m "update"',
        '  git push',
        '',
        'It only works if no other changes have been made to the remote repository since you "downloaded" it',
        ])


    if not os.path.exists('.git'):
        utils.secho("Not a git repository", fg='red')
        return

    output = subprocess.check_output(utils._cmd(f'git add -u')).decode()
    print(output)
    output = subprocess.check_output(utils._cmd(f'git commit -m "update"')).decode()
    print(output)
    output = subprocess.check_output(utils._cmd(f'git push')).decode()
    print(output)
    #_command(f'git clone {exercise}', silent=True)

@gitlab.command('upload')
@crash_report
def gitlab_upload():
    '''"Upload" exercise to GitLab'''
    _gitlab_upload()
