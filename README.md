# Instagram downloader

## Requirements

- python
- pip
- docker
- docker-compose

## Installation

Install python requirements

```
pip install -r requirements.txt
```

Fill a file called `.env` with contents

```
INSTAGRAM_USERNAME="username"
INSTAGRAM_PASSWORD="password"
```

## Usage

Run

```
docker-compose up
```

### Download by hashtag

To search by hashtag and download in images folder execute

```
python src/download.py -k girl,girls -s images/
```

### Download by lists.txt

When you want to search lists you can put the lists in folder lists/*.txt and execute


```
python src/download.py -d lists/ -s images/
```