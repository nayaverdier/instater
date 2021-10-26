# Changelog

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
