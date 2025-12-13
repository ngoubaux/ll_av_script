"""
Console output utilities with colored formatting
"""

from colorama import Fore, Style, init as colorama_init

colorama_init()


def print_step(text: str) -> None:
    """Print a major step in the process"""
    print(Fore.BLUE + "==> " + Style.RESET_ALL + Style.BRIGHT + text + Style.RESET_ALL)


def print_substep(text: str) -> None:
    """Print a minor step in the process"""
    print(Fore.GREEN + "==> " + Style.RESET_ALL + text + Style.RESET_ALL)


def print_error(text: str) -> None:
    """Print an error message"""
    print(
        Fore.RED
        + Style.BRIGHT
        + "X"
        + Style.NORMAL
        + Fore.RED
        + " Error: "
        + Style.RESET_ALL
        + text
    )


def print_warning(text: str) -> None:
    """Print a warning message"""
    print(
        Fore.YELLOW
        + Style.BRIGHT
        + "<!>"
        + Style.NORMAL
        + Fore.YELLOW
        + " Warning: "
        + Style.RESET_ALL
        + text
    )


def print_desc(text: str) -> None:
    """Print a description or detail"""
    print(Style.DIM + text + Style.RESET_ALL)


def print_adding_file(text: str) -> None:
    """Print message about adding a file"""
    print(Style.DIM + "==>" + Style.RESET_ALL + text)
