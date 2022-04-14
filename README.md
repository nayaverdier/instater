# instater

An easy solution for system/dotfile configuration

Loosely based off of Ansible for the task and file organization

## Installation

```bash
pip3 install instater
```

### For Arch users

Using `yay`:

```bash
yay -Sy instater
```

Using makepkg:

```bash
git clone https://aur.archlinux.org/instater.git
cd instater
makepkg -sirc
```

## Usage

See the File Structure Example below to set up variables, files, and tasks.

Once a `setup.yml` file is created, it can be run using

```bash
instater

# or:
instater --setup-file setup.yml
```

To see what changed will be made, but not actually make then, use `--dry-run`:

```bash
instater --dry-run
```

For a complete example, see [dotfiles](https://github.com/nayaverdier/dotfiles)

### File Structure Example

First, create a `setup.yml` file:

```yaml
# Lots of ways to prompt for data at the beginning of execution
vars_prompt:
- name: my_var
- name: custom_prompt
  prompt: Enter something here
- name: private_var
  private: true
- name: private_confirm_var
  private: true
  confirm: true
- name: allow_empty_var
  allow_empty: true

# variables that can be used within tasks/files can be populated
# from a static file, in this case vars/common.yml
vars_files:
- vars/common.yml
# variables can be used within the file names
- "vars/{{ vars_file }}.yml"

# All of the tasks to perform are enumerated
tasks:
- name: Copy file
  # {{ username }} is replaced with the variable `username`
  copy:
    content: "The contents of a new file in here"
    dest: "/home/{{ username }}/Downloads/file1"
    mode: "600"
  # if desired, the output of this task can be registered to use as
  # a condition for subsequent tasks
  register: file1_copy
- name: Run a command if file1 written
  command: "touch /home/{{ username }}/testfile"
  when: file1_copy.changed
```

Then, create a `vars/` directory and `common.yml` within:

```yaml
my_test: 1
some_var: "{{ my_test + 2 }}"
vars_file: "second"
username: something
```

And `vars/second.yml` (since `common.yml` set `vars_file` to `second`):

```yaml
from_second_yml: data in here
```

Now in all of the tasks, `my_test`, `username`, `from_second_yml`, etc will be
present and accessible.

## Tasks

All tasks support the following arguments:

- `name` (string, optional): The name of the task, included in logs
- `when` (string, optional): A Jinja2 statement to determine whether the
  task should be skipped. If the statement evaluates to `True`, the
  task will be executed. Example: `my_variable == 'foo'`
- `register` (string, optional): A variable to store task results under. Can be used
  in conjunction with a subsequent `when` clause, for example `register: my_task`
  can be used in another task as `when: my_task.changed`
- `with_fileglob` (string, optional): If provided, find all files in the instater
  root that match the glob, and create a task with all other

Example of `register` and `when`:

```yaml
- name: Set locale to en_US
  copy:
    content: "en_US.UTF-8 UTF-8\n"
    dest: /etc/locale.gen
  register: locale_gen

- name: Generate locale files
  command: locale-gen
  when: locale_gen.changed
```

Example of `with_fileglob`:

```yaml
- include: "{{ task }}"
  with_fileglob: "applications/*"
```

### `aur` (Arch User Repository, alias of `pacman`)

Install packages from a Arch User Repository

#### Arguments

- `packages` (string, [string]): The packages to install, can be a single package
  or a list of packages
- `become` (string, optional): A user to become while installing packages

Examples:

```yaml
- name: Install python package
  aur:
    packages: python
  become: makepkg
- name: Install python libraries
  aur:
    packages:
    - python-setuptools
    - python-wheel
```

### `command`

Run arbitrary shell commands (can be risky)

#### Arguments

- `command` (string, [string]): The command or commands to execute
- `condition` (string, optional): A command to run prior to the
  `command`, as a condition for whether or not it should actually be
  executed
- `condition_code` (int, optional): The return code from the
  `condition` command to match against. If the `condition` returns this
  code, the `command` will be executed. Defaults to 0
- `become` (string, optional): A user to become while running the
  commands (including the condition command)
- `directory` (string, optional): The working directory to use while
  running the commands

Note that the command and conditions may make use of pipes, for example
`curl -s https://get.sdkman.io | bash`

Examples:

```yaml
- name: Make a curl
  command:
    command: curl https://google.com
- name: Create a file if it doesn't exist
  command:
    command: touch to/file
    condition: ls to/file
    condition_code: 2
    directory: path
- name: Run several commands
  command:
    command:
    - echo "This does nothing"
    - echo "More commands"
```

### `copy`

Copy a file, directory, url, or direct string content to a destination file or directory

#### Arguments

- `dest` (string): The destination file or directory to write to
- `src` (string, optional): The source file or directory to copy
- `content` (string, optional): The exact content that should be copied to the
  dest
- `url` (string, optional): A url to GET and use as the content
- `owner` (string, optional): The owner to set on the file. Note that if a
  parent directory must be created, it may not be given this owner and should
  be created separately
- `group` (string, optional): The group to set on the file. Note that if a
  parent directory must be created, it may not be given this group and should
  be created separately
- `mode` (string, integer, optional): The file permissions to set on the
  destination. Note that if a YAML integer is provided, it must start with a
  `0` to be parsed as octal
- `is_template` (bool, optional): If set to true, the content will be rendered
  using Jinja2 and all available variables before comparing or writing to
  `dest`
- `validate` (string, optional): A command to run to validate the source file
  or content prior to writing it to the destination. Should contain a `%s`
  which will be replaced by a filename to validate. When applied to a
  directory, each file is separately validated

Exactly one of `src`, `content`, or `url` must be provided

Examples:

```yaml
- name: Copy a file
  copy:
    src: files/my_file.txt
    dest: /path/to/destination
- name: Copy a directory
  copy:
    src: files/my_directory
    dest: /path/to/dest
- name: Copy and set owner/group/mode
  copy:
    src: files/executable.sh
    dest: /usr/local/bin/executable.sh
    owner: some_user
    group: some_group
    mode: 0755
- name: Download a url
  copy:
    url: https://raw.githubusercontent.com/nayaverdier/instater/main/README.md
    dest: /path/to/instater/README.md
    owner: my_user
    group: my_user
- name: Copy content directly
  copy:
    content: "{{ hostname }}"
    dest: /etc/hostname
- name: Copy and validate sudoers file
  copy:
    src: files/sudoers
    dest: /etc/sudoers
    mode: 0440
    validate: /usr/sbin/visudo -csf %s
- name: Render jinja template and copy
  copy:
    src: files/my_template
    dest: /path/to/file
    is_template: true
```

### `debug`

Log a debug message

#### Arguments

- `debug` (str): The message to log

#### Example

```yaml
- name: Log execution information
  debug: "Instater root directory: {{ instater_dir }}"
```

### `directory`

Create a directory. Same as passing `directory: true` to the [`file`](#file) task.

#### Arguments

(see [`file`](#file))

#### Example

```yaml
- name: Create example directory
  directory:
    path: "/path/to/directory"
- name: Create a user directory
  directory:
    path: "/home/exampleuser/private_directory"
    owner: exampleuser
    group: exampleuser
    mode: 0700
```

### `file`

Create an empty file, directory, symlink, or hard link on the file system.

#### Arguments

- `path` (string): The path of the file or directory to manage
- `target` (string, optional): When managing a `symlink` or `hard_link`, the
  target file or directory to point to
- `owner` (string, optional): The owner to set on the file. Note that if a
  parent directory must be created, it may not be given this owner and should
  be created separately
- `group` (string, optional): The group to set on the file. Note that if a
  parent directory must be created, it may not be given this group and should
  be created separately
- `mode` (string, integer, optional): The file permissions to set on the
  destination. Note that if a YAML integer is provided, it must start with a
  `0` to be parsed as octal
- `directory` (boolean, optional): If set to `true`, create a directory
- `symlink` (boolean, optional): If set to `true`, create a symlink
- `hard_link` (boolean, optional): If set to `true`, create a hard link

At most one of `directory`, `symlink`, and `hard_link` may be provided

#### Example

```yaml
- name: Create an empty file
  file:
    path: /path/to/file
- name: Create an empty file with owner/group/mode
  file:
    path: /home/myuser/myfile
    owner: myuser
    group: myuser
    mode: 0600
- name: Create a symlink
  file:
    path: /etc/localtime
    target: /usr/share/zoneinfo/America/New_York
    symlink: true
- name: Create a hard link
  file:
    path: /path/to/new/file
    target: /path/to/existing/file
    hard_link: true
- name: Create a directory
  file:
    path: /path/to/my/dir/
    directory: true
- name: Create a directory with owner/group/mode
  file:
    path: /home/myuser/dir/
    owner: myuser
    group: myuser
    mode: 0700
    directory: true
```

### `git`

Clone or update a git repository

#### Arguments

- `repo` (string): The git repo uri to clone
- `dest` (string): The destination path to clone into
- `depth` (integer, optional): Creates a shallow clone with truncated history
- `fetch_tags` (boolean, optional): Whether or not to fetch git tags (defaults to true)
- `become` (string, optional): The UNIX user that should be used to run git commands

#### Example

```yaml
- name: Clone instater
  git:
    repo: https://github.com/nayaverdier/instater
    dest: /home/myuser/Documents/instater
    become: myuser
- name: Clone with truncated history
  git:
    repo: https://github.com/nayaverdier/instater
    dest: /home/myuser/Documents/instater
    depth: 1
    become: myuser
```

### `group`

Create a UNIX group

#### Arguments

- `group` (string): The name of the UNIX group to create

#### Example

```yaml
- name: Create a group
  group: mygroup
```

### `hard_link`

Create a hard link to a file

#### Arguments

(see [`file`](#file))

#### Example

```yaml
- name: Create a hard link
  hard_link:
    path: /path/to/new/linked/file
    target: /path/to/existing/file
```

### `include`

Include another YAML file containing tasks, to allow for better organization of
tasks

#### Arguments

- `include` (string): The path of the YAML file to include (relative to the setup.yml)

#### Example

```yaml
- include: tasks/something.yml
- include: "{{ item }}"
  with_fileglob: "tasks/applications/*"
```

### `pacman`

Install Arch Linux packages using the `pacman`, `yay`, or `makepkg` commands

#### Arguments

- `packages` (string, [string]): The packages to install, can be a single package
  or a list of packages
- `aur` (boolean, optional): If set to true, the packages will be installed from
  the Arch User Repository using `yay` (or `makepkg` as a fallback)
- `become` (string, optional): When `aur` is true, install using a specific user

Examples:

```yaml
- name: Install python package
  pacman:
    packages: python
- name: Install python libraries
  pacman:
    packages:
    - python-setuptools
    - python-wheel
- name: Install instater
  pacman:
    packages:
      - instater
    aur: true
    become: makepkg
```

### `service`

Start, enable, or disable a systemctl service

#### Arguments

- `service` (string): The name of the service to manage
- `started` (boolean, optional): If set to `true`, start the service
- `enabled` (boolean, optional): Whether or not the service should be enabled

#### Example

```yaml
- name: Enable postgres service
  service:
    service: postgresql
    started: true
    enabled: true
- name: Start redis service
  service:
    service: redis
    started: true
```

### `symlink`

Create a symlink to a file or directory

#### Arguments

(see [`file`](#file))

#### Example

```yaml
- name: Create a symlink
  symlink:
    path: /path/to/new/linked/file
    target: /path/to/existing/file
```

### `template`

Copy data, transforming the content as a Jinja2 template prior to writing.
Same as passing `is_template: true` to [`copy`](#copy)

#### Arguments

(see [`copy`](#copy))

#### Example

```yaml
- name: Copy configuration template
  template:
    src: files/some_config
    dest: "/home/{{ username }}/.config/some_config"
    owner: "{{ username }}"
    group: "{{ username }}"
    mode: 0644
```

### `user`

Create a UNIX user

#### Arguments

- `user` (string): The name of the user to create
- `system` (boolean, optional): Whether or not this user is a system user (only
  used when the user needs to be created)
- `create_home` (boolean, optional): Whether or not a home directory for this user
  should be created
- `password` (string, optional): A hashed password to set as the user's password
  (only used when the user needs to be created )
- `shell` (string, optional): The login shell to use for the user
- `groups` (string, [string]): The group or groups to add the user to

#### Example

```yaml
- name: Create primary user
  user:
    user: my_username
    shell: /usr/bin/zsh
    groups: sudo
    password: "{{ login_password | password_hash('sha512') }}"
  when: login_password is defined
- name: Create makepkg user
  user:
    user: makepkg
    groups: makepkg
    system: true
```
