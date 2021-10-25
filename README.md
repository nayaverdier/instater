# instater

An easy solution for system/dotfile configuration

Loosely based off of Ansible for the task and file organization

## Installation

```bash
pip3 install instater
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

### Tasks

All currently defined tasks are listed below

#### aur

#### command

#### copy

#### debug

#### directory

#### file

#### get_url (alias of `copy`)

#### git

#### group

#### hard_link

#### include

#### pacman

#### service

#### symlink

#### template (alias of `copy`)

#### user
