# Changelog

## 0.13.1 2023-11-28

- Add support for python3.12

## 0.13.0 2023-06-06

- Automatically convert int/float from templated variables, instead of being strings
- `become` the `makepkg` user for running `yay` (hardcoded for now)

## 0.12.0 2023-04-24

- Add `pacman_bootstrapped_packages` option to ignore certain packages from the
  manually installed checks
- Add `--quiet` or `-q` flag which does not print any information for skipped
  tasks

## 0.11.0 2022-04-24

- Fix `instater_dir` template variable to be a proper absolute path
  (previously, relative paths could appear like `/path/to/cwd/../another_dir/setup.yml`)
- Add `--explain` flag to show reasoning for each changed/skipped task
- Do not run the pacman package comparison when specifying `--tags`,
  since in that situation the comparison is not complete

## 0.10.0 2022-04-13

- Add `fetch_tags` argument to `git` task

## 0.9.0 2022-04-12

- Add check for manually installed pacman packages when using Arch Linux
- Add `--skip-tasks` argument to skip all tasks (useful for the pacman
  package check)
- Fix bug where relative paths were not resolving when instater was run
  from a directory other than the one containing the setup.yml file

## 0.8.0 2021-11-06

- `command`: Support pipes between two commands

## 0.7.0 2021-11-04

- Better support `when` argument so that undefined variables are
  counted as a falsey variable

## 0.6.0 2021-10-29

- `aur`: Fix bug negating the condition for using `yay` vs `makepkg`

## 0.5.0 2021-10-28

- Add `--version` option to the CLI to display the Instater version
- `aur`: Now an alias of `pacman`, which supports `makepkg`
- `pacman`: Add `aur` and `become` attributes
- `pacman`: Add support for `makepkg` and `yay` installations

## 0.4.0 2021-10-28

- `user`: Support `create_home` argument

## 0.3.0 2021-10-25

- **BREAKING** Use absolute path for the `instater_dir` variable
- Add duration logging for each task and in the overall summary
- Fix tag rendering to support `{{ item }}` in tags
- Add a `filename` jinja filter to extract filenames without extensions
- Document all tasks
- `aur`/`pacman`: Support checking for package group installation
- **BREAKING** `debug`: Remove the `msg` argument(pass the debug message
  directly to `debug`)
- **BREAKING** `get_url`: Remove task as it is identical to `copy`

## 0.2.0 2021-10-24

- Initial release was missing `tasks` module, fixed in 0.2.0
- Fix circular dependency issue when packaged
- Update README with all existing tasks

## 0.1.0 2021-10-24

- Initial release
