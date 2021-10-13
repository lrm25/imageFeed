# imageFeed

Pull images from reddit's spaceporn subreddit

Tested on Ubuntu Linux w/Gnome (but should work on any Linux w/Gnome) and Windows 10

## To create and use virtual environment:

### Venv
```
python3 -m venv env
```
#### Linux
```
source env/bin/activate
```
#### Windows
```
.\env\bin\activate
```

### pipenv (after installing it)

pipenv --python 3.7.4

## To run jupyter notebook file

pipenv install beautifulsoup4 jupyter
pipenv run jupyter notebook

## Install scrapy

`pip install scrapy`

or

`pipenv install scrapy`

## To run scrapy

Enter the program subfolder and run:

`scrapy crawl space-porn`

or

`pipenv run scrapy crawl space-porn`

For cleaner output:

`scrapy crawl --nolog space-porn`
