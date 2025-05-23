import os
import sys
import platform
import webbrowser
import urllib.parse
import pyperclip
import click
from functools import wraps

from .logger import logger
from . import crash
from . import config as cfg
from .system import package_version
from . import terminal as term
from typing import Callable
from . import system


class Crash(Exception):
    """
    Package dummy Exception raised when a crash is encountered.
    """
    pass


class UpdateCrash(Crash):
    """
    Package dummy Exception raised when a crash during update.
    """
    pass


def gather_crash_info(include_log=True) -> str:
    """
    Gathers information about the system and the crash.
    """
    info = f"Python: {sys.executable}\n"
    info += f'Version of franklin: {package_version("franklin")}\n'    
    info += f'Version of franklin-educator: {package_version("franklin-educator")}\n'
    for k, v in platform.uname()._asdict().items():
        info += f"{k}: {v}\n"
    info += f"Platform: {platform.platform()}\n"
    info += f"Machine: {platform.machine()}\n"
    info += f"Processor: {platform.processor()}\n"
    info += f"Python Version: {platform.python_version()}\n"
    info += f"Python Compiler: {platform.python_compiler()}\n"
    info += f"Python Build: {platform.python_build()}\n"
    info += f"Python Implementation: {platform.python_implementation()}\n"

    if include_log:
        if os.path.exists('franklin.log'):
            with open('franklin.log', 'r') as f:
                log = f.read()
        info += f"\n\nFranklin log:\n{log}\n"

    return info


def crash_email() -> None:
    """
    Open the email client with a prefilled email to the maintainer of Franklin.
    """

    preamble = ("This email is prefilled with information of the crash you can send to the maintainer of Franklin.").upper()

    info = gather_crash_info(include_log=False)

    log = ''
    if not system.system() == 'Windows':
        if os.path.exists('franklin.log'):
            with open('franklin.log', 'r') as f:
                log = f.read()

    subject = urllib.parse.quote("Franklin CRASH REPORT")
    body = urllib.parse.quote(f"{preamble}\n\n{info}\n{log}")
    webbrowser.open(f"mailto:?to={cfg.maintainer_email}&subject={subject}&body={body}", new=1)


def crash_report(func: Callable) -> Callable:
    """
    Decorator to handle crashes and open an email client with a prefilled email to the maintainer of Franklin.

    Parameters
    ----------
    func : 
        Function to decorate.

    Returns
    -------
    :
        Decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):


        def msg_and_exit():
            term.secho(f"\nFranklin encountered an unexpected problem.", fg='red')
            term.secho(f'\nPlease open an email to {cfg.maintainer_email} with subject "Franklin crash". The email body should contain the crash information.')
            click.pause("Press Enter to copy the crash information to your clipboard.")
            pyperclip.copy(gather_crash_info())
            sys.exit(1)   

        if os.environ.get('DEVEL', None):
            return func(*args, **kwargs)
        try:
            ret = func(*args, **kwargs)
        except KeyboardInterrupt as e:
            logger.exception('KeyboardInterrupt')
            if 'DEVEL' in os.environ:
                raise e
            raise click.Abort()
        except crash.UpdateCrash as e:
            logger.exception('Raised: UpdateCrash')
            for line in e.args:
                term.secho(line, fg='red')
            sys.exit(1)
        except crash.Crash as e:
            logger.exception('Raised: Crash')
            if 'DEVEL' in os.environ:
                raise e
            logger.exception('Raised: UpdateCrash')
            for line in e.args:
                term.secho(line, fg='red')
            msg_and_exit()         
        except SystemExit as e:
            raise e
        except click.Abort as e:
            logger.exception('Raised: Abort')
            raise e
        except:
            logger.exception('CRASH')
            msg_and_exit()
            raise
        return ret
    return wrapper
