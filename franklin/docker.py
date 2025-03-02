import platform
import subprocess
from subprocess import run, check_output, Popen, PIPE, DEVNULL
import json
import sys
import os
import re
import click
import requests
import shutil
import logging
import time
import psutil
import sysconfig
from functools import wraps
from . import utils
from .utils import AliasedGroup
from .config import REGISTRY_BASE_URL, GITLAB_GROUP, REQUIRED_GB_FREE_DISK, PG_OPTIONS, MIN_WINDOW_WIDTH
from . import cutie
from .gitlab import get_course_names, get_exercise_names
from .logger import logger
from pathlib import Path, PureWindowsPath, PurePosixPath

def _docker_desktop_settings(**kwargs):

    home = Path.home()
    if platform.system() == 'Darwin':
        json_settings = home / 'Library/Group Containers/group.com.docker/settings-store.json'
    elif platform.system() == 'Windows':
        json_settings = home / '/AppData/Roaming/Docker/settings-store.json'
    elif platform.system() == 'Linux':
        json_settings = home / '.docker/desktop/settings-store.json'

    with open(json_settings, 'r') as f:
        settings = json.load(f)

    if not kwargs:
        return settings
    
    for key, value in kwargs.items():
        settings[key] = value

    with open(json_settings, 'w') as f:
        json.dump(settings, f)


def _install_docker_desktop():

    utils.secho(f"\nInstalling Docker desktop.", fg='green')

    architecture = sysconfig.get_platform().split('-')[-1]
    assert architecture in ['amd64', 'arm64']

    if platform.system() == 'Windows':
        if architecture == 'arm64':
            download_url = 'https://desktop.docker.com/win/main/arm64/Docker%20Desktop%20Installer.exe'
        else:
            download_url = 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe'
        installer = 'Docker Desktop Installer.exe'
    elif platform.system() == 'Darwin':
        if architecture == 'arm64':
            download_url = 'https://desktop.docker.com/mac/main/arm64/Docker.dmg'
        else:
            download_url = 'https://desktop.docker.com/mac/main/amd64/Docker.dmg'
        installer = 'Docker.dmg'
    else:
        url = 'https://docs.docker.com/desktop/linux/install/'
        utils.echo(f'Download from {url} and install before proceeding.')
        sys.exit(1)

    response = requests.get(download_url, stream=True)
    if not response.ok:
        utils.echo(f"Could not download Docker Desktop. Please download from {download_url} and install before proceeding.")
        sys.exit(1)

    file_size = response.headers['Content-length']
    with open(installer, mode="wb") as file:
        nr_chunks = int(file_size) // (10 * 1024) + 1
        with click.progressbar(length=nr_chunks, label='Downloading', **PG_OPTIONS) as bar:
            for chunk in response.iter_content(chunk_size=10 * 1024):
                file.write(chunk)
                bar.update(1)
    
    if platform.system() == 'Windows':

        utils.echo("Installing:")
        utils.echo()
        utils.secho('='*75, fg='red')
        utils.echo('  You will be prompted for install permission. Accept and then follow the installation procedure. Once completed, return to this window.', fg='red')
        utils.secho('='*75, fg='red')
        utils.echo()
        click.pause()

        run(installer, check=True)

        utils.echo(" - Removing installer...")
        os.remove(installer)

    elif platform.system() == 'Darwin':
        cmd = utils._cmd(f'hdiutil attach -nobrowse -readonly {installer}')
        output = check_output(cmd).decode().strip()

        # Extract the mounted volume name from the output
        mounted_volume_name = re.search(r'/Volumes/([^ ]*)', output.strip()).group(1)

        utils.echo("Installing:")
        utils.echo()
        utils.secho('='*75, fg='red')
        utils.echo('  Press Enter and then drag the Docker to the Applications folder.', fg='red')
        utils.secho('='*75, fg='red')
        utils.echo()
        click.pause('Press Enter...')

        check_output(utils._cmd(f'open /Volumes/{mounted_volume_name}')).decode().strip()

        utils.echo(" - Copying to Applications...")
        prev_size = ''
        for _ in range(1000):
            cmd = f'du -s /Applications/Docker.app'
            logger.debug(cmd)
            cmd = cmd.split()
            cmd[0] = shutil.which(cmd[0])
            output = run(cmd, stdout=PIPE, stderr=DEVNULL, timeout=1, check=False).stdout.decode().strip()
            if output:
                size = output.split()[0]
                if size == prev_size:
                    break
                prev_size = size
            time.sleep(5)

        time.sleep(5)

        # # allow some time for the app to be copied and validated...
        # with click.progressbar(length=10, label='Validating Docker Desktop', fill_char='#') as bar:
        #     for _ in range(10):
        #         time.sleep(1)
        #         bar.update(1)

        utils.echo(" - Unmounting...")

        if os.path.exists('/Volumes/{mounted_volume_name}'):
            _run(f'hdiutil detach /Volumes/{mounted_volume_name}/')

        utils.echo(" - Removing installer...")
        os.remove(installer)

        utils.echo(" - Setup...")
        # Disable the "Open on startup"
        _docker_desktop_settings(OpenUIOnStartupDisabled=True)


#  start /w "" "Docker Desktop Installer.exe" uninstall
#  /Applications/Docker.app/Contents/MacOS/uninstall

def _start_docker_desktop():
    if not _status() == 'running':
        utils.logger.debug('Starting/restarting Docker Desktop')
        _restart()
    for w in range(10):
        if _status() == 'running':                
            break
        time.sleep(1)
    utils.echo()


def _failsafe_start_docker_desktop():

    if shutil.which('docker') and _status() == 'running':
        return

    if not shutil.which('docker'):
         _install_docker_desktop()

    _start_docker_desktop()

    if not _status() == 'running':
        utils.logger.debug('Killing all Docker Desktop processes')
        _kill_all_docker_desktop_processes()
        _start_docker_desktop()

    if not _status() == 'running':
        utils.logger.debug('Could not start Docker Desktop. Please start Docker Desktop manually')
        utils.secho("Could not start Docker Desktop. Please start Docker Desktop manually.", fg='red')
        sys.exit(1)


def ensure_docker_running(func):
    """
    Decorator for functions that require Docker Desktop to be running.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        _failsafe_start_docker_desktop()
        return func(*args, **kwargs)
    return wrapper

def irrelevant_unless_docker_running(func):
    """
    Decorator for functions that require Docker Desktop to be running.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not _status() == 'running':
            utils.secho("Docker is not running")
            return None
        return func(*args, **kwargs)
    return wrapper


def _image_exists(image_url):
    for image in _images(return_json=True):
        if image['Repository'].startswith(image_url):
            return True
    return False


def _command(command, silent=False, return_json=False):
    if silent:
        return subprocess.run(utils.format_cmd(command), check=False, stdout=DEVNULL, stderr=DEVNULL)
    if return_json:
        result = []
        for line in subprocess.check_output(utils.format_cmd(command + ' --format json')).decode().strip().splitlines():
            result.append(json.loads(line))
        return result
    else:
        return subprocess.check_output(utils.format_cmd(command)).decode().strip()


def _table(header, table, ids, min_widths=None, select=True):

    col_widths = [max(len(x) for x in col) for col in zip(*table)]

    max_width = shutil.get_terminal_size().columns - 4 * len(col_widths) - 4 * int(select) - 2

    if min_widths is None:
        min_widths = [15] * len(col_widths)
    elif None in min_widths:
        non_col_widths = sum(c for c, m in zip(col_widths, min_widths) if m is None)
        leeway = (max_width - sum(x for x in min_widths if x is not None))
        col_widths = [int(c / non_col_widths * leeway) if m is None else m for c, m in zip(col_widths, min_widths)]
    elif sum(col_widths) > max_width:
        leeway = max_width - sum(min_widths)
        if leeway > 0:
            col_widths =  [min_widths[i] + int((w/sum(col_widths)*leeway)) for i, w in enumerate(col_widths)]

    table_width = sum(col_widths) + 4 * len(col_widths) + 2

    utils.echo("Move: Arrow up/down, Toggle-select: Space, Confirm: Enter, Abort: Ctrl-C\n"*int(select))
    utils.echo('    '*int(select)+'| '+'| '.join([x[:w].ljust(w+2) for x, w in zip(header, col_widths)]), nowrap=True)
    click.echo('-'*(table_width-4*int(not select)))
    rows = []
    for row in table:
        rows.append('| '+'| '.join([x[:w].ljust(w+2) for x, w in zip(row, col_widths)]))

    if not select:
        return rows

    captions = []
    selected_indices = cutie.select_multiple(
        rows, caption_indices=captions, 
        # hide_confirm=False
        hide_confirm=True
    )
    return [ids[i]for i in selected_indices]


###########################################################
# docker subcommands
###########################################################

@click.group(cls=AliasedGroup)
def docker():
    """Docker commands."""
    pass


def _pull(image_url):
    subprocess.run(utils.format_cmd(f'docker pull {image_url}:main'), check=False)


@click.argument("url")
@docker.command()
@ensure_docker_running
def pull(url):
    """Pull docker image.
    
    URL is the Docker image URL.
    """
    _pull(url)


def _restart():
    _command(('docker desktop restart'), silent=True)

@docker.command()
def restart():
    """Restart Docker Desktop"""
    _restart()


def _start():
    _command('docker desktop start', silent=True)

@docker.command()
def start():
    """Start Docker Desktop"""
    _start()


def _stop():
    _command('docker desktop stop', silent=True)

@docker.command()
@irrelevant_unless_docker_running
def stop():
    """Stop Docker Desktop"""
    _stop()


def _status():
    stdout = subprocess.run(utils.format_cmd('docker desktop status --format json'), 
                            check=False, stderr=DEVNULL, stdout=PIPE).stdout.decode()
    if not stdout:
        return 'not running'
    # stdout = subprocess.check_output(utils.format_cmd('docker desktop status --format json')).decode()
    data = json.loads(stdout)
    return data['Status']

@docker.command()
def status():
    "Docker Desktop status"
    s = _status()
    fg = 'green' if s == 'running' else 'red'
    utils.secho(s, fg=fg, nowrap=True)


def _update(return_json=False):
    return _command('docker desktop update', return_json=return_json)

@docker.command()
def update():
    """Update Docker Desktop"""
    _update()


def _version(return_json=False):
    _command('docker desktop version --format json', return_json=return_json)

@docker.command()
def version():
    """Get Docker Desktop version"""
    _version()


###########################################################
# docker prune subcommands
###########################################################


@docker.group(cls=AliasedGroup)
def prune():
    """Prune Docker elements"""
    pass


def _prune_containers():
    _command(f'docker container prune --all --force --filter="Name={REGISTRY_BASE_URL}*"', silent=True)

@prune.command('containers')
def prune_containers():
    """
    Remove all stopped containers.
    """
    _prune_containers()


def _prune_images():
    _command(f'docker image prune --all --force --filter="Name={REGISTRY_BASE_URL}*"', silent=True)

@prune.command('images')
def prune_images():
    """
    Remove all unused images.
    """
    _prune_images()


# def _prune_cache():
#     _command(f'docker system prune --all --force --filter="Name={REGISTRY_BASE_URL}*"', silent=True)

# @docker.command('cache')
# def prune_cache():
#     """
#     Remove all dangling images.
#     """
#     _prune_cache()


def _prune_all():
    _command(f'docker system prune --all --force --filter="Name={REGISTRY_BASE_URL}*"', silent=True)

@prune.command('all')
def prune_all():
    """
    Remove everything you are not using right now: all stopped 
    containers, all networks not used by at least one container, 
    all dangling images, unused build cache.
    """
    _prune_all()





# def _build(directory=Path.cwd(), tag=None):

#     if tag is None:
#         check_output('')
#     git config --get remote.origin.url

#     tag = f'-t {tag}' if tag else ''
#     subprocess.run(utils.format_cmd(f'docker build --platform=linux/amd64 {directory} {tag}'), check=False)

#     git config --get remote.origin.url

#  -t franklin/genomic-thinking/arg-dashboard for build
# #docker build --platform=linux/amd64 -t kaspermunch/jupyter-linux-amd64:latest .

# @click.argument("directory")
# @click.option("--tag", help="Tag for the image")
# @docker.command()
# def build(directory, tag=None):
#     """
#     Build image from Dockerfile. Use for testing that the image builds correctly.
#     """
#     _build(directory, tag)


def _run(image_url):

    if platform.system() == "Windows":
        popen_kwargs = dict(creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        popen_kwargs = dict(start_new_session = True)

    ssh_mount = Path.home() / '.ssh'
    anaconda_mount = Path.home() / '.anaconda'
    cwd_mount_source = Path.cwd()
    cwd_mount_target = Path.cwd()
    ssh_mount.mkdir(exist_ok=True)
    anaconda_mount.mkdir(exist_ok=True)
    if platform.system() == 'Windows':
        ssh_mount = PureWindowsPath(ssh_mount)
        anaconda_mount = PureWindowsPath(anaconda_mount)
        cwd_mount_source = PureWindowsPath(cwd_mount_source)
        cwd_mount_target = PurePosixPath(cwd_mount_source)
        parts = cwd_mount_target.parts
        assert ':' in parts[0]
        cwd_mount_target = PurePosixPath('/', *(cwd_mount_target.parts[1:]))

    cmd = (
        # rf"docker run --rm"
        rf"docker run --rm --pull=always"
        rf" --mount type=bind,source={ssh_mount},target=/tmp/.ssh"
        rf" --mount type=bind,source={anaconda_mount},target=/root/.anaconda"
        rf" --mount type=bind,source={cwd_mount_source},target={cwd_mount_target}"
        rf" -w {cwd_mount_target} -i -p 8050:8050 -p 8888:8888 {image_url}:main"
    )
    logger.debug(cmd)

    cmd = cmd.split()
    cmd[0] = shutil.which(cmd[0])
    docker_run_p = Popen(cmd, 
                        stdout=DEVNULL, stderr=DEVNULL, 
                        **popen_kwargs)
    return docker_run_p

@click.argument("url")
@docker.command()
@ensure_docker_running
def run(url):
    """
    Run container from image. Use for testing that the image runs correctly.    
    """
    _run(url)


###########################################################
# docker kill subcommands
###########################################################

@docker.group(cls=AliasedGroup)
def kill():
    """Kill Docker elements"""
    pass

def _kill_container(container_id):
    """Kill a running container."""
    cmd = utils._cmd(f'docker kill {container_id}', log=False)
    Popen(cmd, stderr=DEVNULL, stdout=DEVNULL)

# def kill_container(container_id):
#     _kill_container(container_id)


@kill.command('docker')
def _kill_all_docker_desktop_processes():
    """
    Kills Docker the hard way (tute la famiglia).
    """
    for process in psutil.process_iter():
        if 'docker' in process.name().lower():
            pid = psutil.Process(process.pid)
            if not 'SYSTEM' in pid.username():
                process.kill()
                

def _container_list(callback=None):

    current_containers = _containers(return_json=True)
    if not current_containers:
        click.echo("\nNo running containers\n")
        return

    course_names = get_course_names()
    exercise_names = {}

    header = ['Course', 'Exercise', 'Started']
    table = []
    ids = []
    prefix = f'{REGISTRY_BASE_URL}/{GITLAB_GROUP}'
    for cont in current_containers:
        if cont['Image'].startswith(prefix):
            rep = cont['Image'].replace(prefix, '')
            if rep.endswith(':main'):
                rep = rep[:-5]
            if rep.startswith('/'):
                rep = rep[1:]
            course_label, exercise_label = rep.split('/')
            if exercise_label not in exercise_names:
                exercise_names.update(get_exercise_names(course_label))
            course_name = course_names[course_label]
            exercise_name = exercise_names[exercise_label]
            ids.append(cont['ID'])
            table.append((course_name, exercise_name , cont['RunningFor'].replace(' ago', '')))

    if callback is None:
        for row in _table(header, table, ids, min_widths=[None, None, 20], select=True):
            utils.echo(row)
        utils.echo()
        return
    
    utils.secho("\nChoose containers to kill:", fg='green')

    for cont_id in _table(header, table, ids, min_widths=[None, None, 20], select=True):
        callback(cont_id, force=True)


@kill.command('containers')
@click.argument("container_id", required=False)
@irrelevant_unless_docker_running
def _kill_selected_containers(container_id=None):

    if container_id:
        _kill_container(container_id)
        return
    
    _container_list(callback=_kill_container)


###########################################################
# docker prune subcommands
###########################################################

# @click.option("--containers/--no-containers", default=True, help="Prune containers")
# @click.option("--volumes/--no-volumes", default=True, help="Prune volumes")
# @docker.command()
# def prune(containers, volumes):
#     """Prune docker containers and volumes."""
#     if containers and volumes:
#         _docker.prune_all()
#     elif containers:
#         _docker.prune_containers()
#     elif volumes:
#         _docker.prune_volumes()

# @click.option("--force/--no-force", default=False, help="Force removal")
# @click.argument('image')
# @docker.command()
# def remove(image, force):
#     """Remove docker image.
    
#     IMAGE is the id of the image to remove.
#     """

#     _docker.rm_image(image, force)

# @docker.command()
# def cleanup():
#     """Cleanup everything."""

#     for image in _docker.images():
#         if image['Repository'].startswith(REGISTRY_BASE_URL):
#             _docker.rm_image(image['ID'])
#     _docker.prune_containers()
#     _docker.prune_volumes()
#     _docker.prune_all()

###########################################################
# docker show subcommands
###########################################################


@docker.group(cls=AliasedGroup)
def show():
    """Show Docker elements"""
    pass


def _containers(return_json=False):
    return _command('docker ps', return_json=return_json)

@show.command()
@ensure_docker_running
def containers():
    """Show running docker containers."""
    _container_list()
    # utils.echo(_containers(), nowrap=True)


def _storage(verbose=False):
    if verbose:
        return _command(f'docker system df -v')
    return _command(f'docker system df')

@click.option("--verbose/--no-verbose", default=False, help="More detailed output")
@show.command()
@ensure_docker_running
def storage(verbose):
    """Show Docker's disk usage."""
    utils.echo(_storage(verbose), nowrap=True)


def _logs(return_json=False):
    _command('docker desktop logs', return_json=return_json)

@show.command()
def logs():
    _logs()


def _volumes(return_json=False):
    return _command('docker volume ls', return_json=return_json)

@show.command()
@ensure_docker_running
def volumes():
    """List docker volumes."""
    utils.echo(_volumes(), nowrap=True)


def _images(return_json=False):
    return _command('docker images', return_json=return_json)

@show.command()
@ensure_docker_running
def images():
    """List docker images."""
    # utils.echo(_images(), nowrap=True)
    _image_list()


###########################################################
# docker remove subcommands
###########################################################

def _rm_image(image, force=False):
    if force:
        _command(f'docker image rm -f {image}', silent=True)
    else:
        _command(f'docker image rm {image}', silent=True)


@docker.group(cls=AliasedGroup)
@ensure_docker_running
def remove():
    """Remove Docker images and volumes"""
    pass

def _image_list(callback=None):
    img = _images(return_json=True)
    if not img:
        click.echo("\nNo images to remove\n")
        return

    course_names = get_course_names()
    exercise_names = {}

    # header = ['Course', 'Exercise', 'Created', 'Size', 'ID']
    header = ['Course', 'Exercise', 'Age', 'Size']
    table = []
    ids = []
    prefix = f'{REGISTRY_BASE_URL}/{GITLAB_GROUP}'
    for img in _images(return_json=True):
        if img['Repository'].startswith(prefix):

            rep = img['Repository'].replace(prefix, '')
            if rep.startswith('/'):
                rep = rep[1:]
            course_label, exercise_label = rep.split('/')
            if exercise_label not in exercise_names:
                exercise_names.update(get_exercise_names(course_label))
            course_name = course_names[course_label]
            exercise_name = exercise_names[exercise_label]
            course_field = course_name
            exercise_field = exercise_name
            # course_field = course_name[:30]+'...' if len(course_name) > 33 else course_name
            # exercise_field = exercise_name[:30]+'...' if len(exercise_name) > 33 else exercise_name
            # table.append((course_field, exercise_field , img['CreatedSince'], img['Size'], img['ID']))
            ids.append(img['ID'])
            table.append((course_field, exercise_field , img['CreatedSince'].replace(' ago', ''), img['Size'].replace("GB", " GB")))

    if callback is None:
        for row in _table(header, table, ids, min_widths=[None, None, 9, 9], select=False):
            utils.echo(row)
        utils.echo()
        return

    utils.secho("\nChoose images to remove:", fg='green')

    for img_id in _table(header, table, ids, min_widths=[None, None, 9, 9], select=True):
        callback(img_id, force=True)


@remove.command('images')
@click.argument("image_id", required=False)
def _remove_selected_images(image_id=None):
    
    if image_id:
        _rm_image(image_id)
        return

    _image_list(callback=_rm_image)


    # img = _images(return_json=True)
    # if not img:
    #     click.echo("\nNo images to remove\n")
    #     return

    # course_names = get_course_names()
    # exercise_names = {}

    # # header = ['Course', 'Exercise', 'Created', 'Size', 'ID']
    # header = ['Course', 'Exercise', 'Age', 'Size']
    # table = []
    # ids = []
    # prefix = f'{REGISTRY_BASE_URL}/{GITLAB_GROUP}'
    # for img in _images(return_json=True):
    #     if img['Repository'].startswith(prefix):

    #         rep = img['Repository'].replace(prefix, '')
    #         if rep.startswith('/'):
    #             rep = rep[1:]
    #         course_label, exercise_label = rep.split('/')
    #         if exercise_label not in exercise_names:
    #             exercise_names.update(get_exercise_names(course_label))
    #         course_name = course_names[course_label]
    #         exercise_name = exercise_names[exercise_label]
    #         course_field = course_name
    #         exercise_field = exercise_name
    #         # course_field = course_name[:30]+'...' if len(course_name) > 33 else course_name
    #         # exercise_field = exercise_name[:30]+'...' if len(exercise_name) > 33 else exercise_name
    #         # table.append((course_field, exercise_field , img['CreatedSince'], img['Size'], img['ID']))
    #         ids.append(img['ID'])
    #         table.append((course_field, exercise_field , img['CreatedSince'].replace(' ago', ''), img['Size'].replace("GB", " GB")))

    # utils.secho("\nChoose images to remove:", fg='green')

    # for img_id in _table(header, table, ids, min_widths=[None, None, 9, 9]):
    #     _rm_image(img_id, force=True)


@remove.command('everything')
def _remove_everything():
    _command(f'docker system prune --all --force --filter="Name={REGISTRY_BASE_URL}*"', silent=True)
