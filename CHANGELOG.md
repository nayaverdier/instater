# Changelog

## 0.5.0 2021-10-28

- Add `--version` option to the CLI to display the Instater version
- **BREAKING** `aur`: Delete task (behavior moved into `pacman`)
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
