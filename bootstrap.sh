#!/usr/bin/env bash
#
# Bootstrap script for setting up an OSX machine of ll_av_script
#

# helpers
function echo_ok() { echo -e '\033[1;32m'"$1"'\033[0m'; }
function echo_warn() { echo -e '\033[1;33m'"$1"'\033[0m'; }
function echo_error() { echo -e '\033[1;31mERROR: '"$1"'\033[0m'; }


if git rev-parse --git-dir > /dev/null 2>&1; then
	echo_ok "Looking for updates."
	git fetch
	if [  "$(git rev-parse HEAD)" != "$(git rev-parse @{u})" ]; then
		echo_ok "Script needs to be updated."
		git reset --hard
		git pull -f --rebase
		echo_ok "Start bootstrap script again."
		exec ./bootstrap.sh
	fi
fi

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
	/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
	(echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> ${HOME}/.zprofile
	eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Update homebrew recipes
brew update

PACKAGES=(
	git
	cask
	curl
	python3
	ffmpeg
    exiftool
	pipenv
)

echo_ok "Installing packages..."
brew install "${PACKAGES[@]}"

echo_ok "Cleaning up..."
brew cleanup

# echo_ok "Installing Python packages..."
# PYTHON_PACKAGES=(
# 	ffmpeg-python
#     PyYAML
#     pyexiftool
# 	colorama
# )
# python3 -m pip install "${PYTHON_PACKAGES[@]}"

project_name="ll_av_script"
project_folder=""
echo_ok "Fetching last version of the ${project_name} ..."
if [ -x $project_name ]; then
	if ! git -C ${project_name} rev-parse --git-dir > /dev/null 2>&1; then
		backup_name="$(mktemp -d ll_av_script.XXXX)"
		echo_ok "Backup existing ${project_name} folder to ${backup_name}..."
		mv "${project_name}" "${backup_name}"
	else
		echo_ok "Using a previous ${project_name} folder..."
		cd ${project_name}
	fi
fi


if ! git rev-parse --git-dir > /dev/null 2>&1; then
  	git clone https://goubsi@bitbucket.org/goubsi/ll_av_script.git ${project_name} --depth 1
	cd ${project_name}
fi

project_folder="$(pwd)"

echo_ok "Setting up ${project_name} env ..."
if [ ! -d "inputs" ]; then
	mkdir inputs
fi
if [ ! -d "outputs" ]; then
	mkdir outputs
fi
#python3 -m pip install -r requirements.txt
pipenv install
chmod +x ll_av_script.py
chmod +x ll_sd2towav.py

echo_ok "Bootstrapping ${project_name} complete"
echo_ok "Script is installed in ${project_folder}"
echo_ok "You can executed by this command: cd ${project_folder}; ./ll_av_script.py"
echo_ok "                                  cd ${project_folder}; ./ll_sd2towav.py"
