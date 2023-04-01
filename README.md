# imageFeed

Pull latest image from reddit's spaceporn subreddit

## Installation

### Create and use virtual environment:

#### Linux

```
python3 -m venv env
source env/bin/activate
```

#### Windows

```
python -m venv env
env\Scripts\activate
```

### Install dependencies

#### Jupyter notebook

`pip install beautifulsoup4 jupyter`

#### Scrapy

`pip install scrapy`

## Usage

## Jupyter notebook

pipenv run jupyter notebook

## Scrapy

Enter the `imagefeed` subfolder and run:

`scrapy crawl space-porn`

For cleaner output:

`scrapy crawl --nolog space-porn`

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
