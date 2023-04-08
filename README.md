# imageFeed

Pull latest image from reddit's spaceporn subreddit

## Installation

### Create and use virtual environment:

#### Linux

Tested on Ubuntu Linux w/Gnome (but should work on any Linux w/Gnome) and Windows 10

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

#### Windows

```
python -m venv env
env\Scripts\activate
```

### Install dependencies

#### All with requirements.txt

`pip install -r requirements.txt`

#### Specific for Jupyter notebook

`pip install beautifulsoup4 jupyter`

#### Specific for crapy

`pip install scrapy`

## Usage

### Jupyter notebook

`pipenv run jupyter notebook`

### Scrapy

Enter the `imagefeed` subfolder and run:

`scrapy crawl space-porn`

For cleaner output:

`scrapy crawl --nolog space-porn`

Print usage:

`scrapy crawl --nolog space-porn -a help=true`

### Dockerfile

Build with:

`docker build -t <desired name> .`

Run with:

`docker run -t <desired image folder>:/image <image name>`

## Development

### Linting

Install linter with `pip install pylint`
Go to `space_porn_spider.py` and run `pylint space_porn_spider.py`

### Testing

Run the following:

```
pip install pytest mock
pytest
```
