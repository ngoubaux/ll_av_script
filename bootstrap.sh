#!/usr/bin/env bash
#
# Bootstrap script for setting up an OSX machine of ll_av_script
#

# helpers
function echo_ok() { echo -e '\033[1;32m'"$1"'\033[0m'; }
function echo_warn() { echo -e '\033[1;33m'"$1"'\033[0m'; }
function echo_error() { echo -e '\033[1;31mERROR: '"$1"'\033[0m'; }

echo_ok "Install starting. You may be asked for your password (for sudo)."

# requires xcode and tools!
xcode-select -p || exit "XCode must be installed! (use the app store)"

# homebrew
export HOMEBREW_CASK_OPTS="--appdir=/Applications"
if hash brew &>/dev/null; then
	echo_ok "Homebrew already installed. Getting updates..."
	brew update
	brew doctor
else
	echo_warn "Installing homebrew..."
	ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
fi

# Update homebrew recipes
brew update

PACKAGES=(
	git
	cask
	curl
	graphviz
	pipenv
	python3
	pyenv
	pyenv-virtualenv
	wget
	ffmpeg
    exiftool
    vlc
)

echo_ok "Installing packages..."
brew install "${PACKAGES[@]}"

echo_ok "Cleaning up..."
brew cleanup

echo_ok "Installing Python packages..."
PYTHON_PACKAGES=(
	ffmpeg-python
    PyYAML
    pyexiftool
)
python3 -m pip install "${PYTHON_PACKAGES[@]}"

echo_ok "Bootstrapping complete"
