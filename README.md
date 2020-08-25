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

Download models and protos in models directory

```
cd models/
wget https://github.com/spmallick/learnopencv/raw/master/AgeGender/opencv_face_detector.pbtxt
wget https://github.com/spmallick/learnopencv/raw/master/AgeGender/opencv_face_detector_uint8.pb
wget https://github.com/spmallick/learnopencv/raw/master/AgeGender/age_deploy.prototxt
wget https://github.com/spmallick/learnopencv/raw/master/AgeGender/gender_deploy.prototxt
wget https://www.dropbox.com/s/iyv483wz7ztr9gh/gender_net.caffemodel
wget https://www.dropbox.com/s/xfb20y596869vbb/age_net.caffemodel
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

### Download by hashtag and classify at the same time

To search by hashtag and classify gender and keep only those images please execute

```
python src/download.py -k girl,girls -s images/ -g female
```