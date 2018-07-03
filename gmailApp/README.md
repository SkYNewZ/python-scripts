# Gmail App
Simple app to mass deletion or trashing email

# Intall
```sh
$ git clone git@github.com:SkYNewZ/python-scripts.git
$ cd python-scripts/gmailApp

# create a virtual env
$ virtualenv my-custom-venv

# active your virtual env
$ source my-custom-venv/bin/activate

# install
$ python setup.py install
$ pip install -r requirements.txt
```

# Usage
* Follow [this guide](https://developers.google.com/gmail/api/quickstart/python) in order to obtain credentials
* You can run `python main.py --help`
```
usage: main.py [-h] --search SEARCH [--mode MODE]

Tools for mass deleting mails

optional arguments:
  -h, --help       show this help message and exit
  --search SEARCH  Search filter like on Gmail search bar
  --mode MODE      Trash messages or delete definitively. Usage: --mode=trash
                   or --mode=delete. Default: trash
```