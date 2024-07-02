from colorama import Fore, Back, Style, init as colorama_init
from pprint import pprint

colorama_init()

def print_step(str):
    print(Fore.BLUE + "==> " + Style.RESET_ALL + Style.BRIGHT + str + Style.RESET_ALL)

def print_substep(str):
    print(Fore.GREEN + "==> " + Style.RESET_ALL + str + Style.RESET_ALL)

def print_error(str):
    print(
        Fore.RED
        + Style.BRIGHT
        + "X"
        + Style.NORMAL
        + Fore.RED
        + " Error: "
        + Style.RESET_ALL
        + str
    )

def print_warning(str):
    print(
        Fore.YELLOW
        + Style.BRIGHT
        + "<!>"
        + Style.NORMAL
        + Fore.YELLOW
        + " Warning: "
        + Style.RESET_ALL
        + str
    )

def print_desc(str):
    print(Style.DIM + str + Style.RESET_ALL)


def print_addingg_file(str):
    print(Style.DIM + "==>" + Style.RESET_ALL + str)
