# Python saved posts grabber

Grabs the saved posts in reddit and can save in mongodb

# Setup Usage

requirements:

1. python 3.8+
2. mongodb
3. reddit account and client credentials

```
$ pip install -r requirements.txt
$ cp .env.template .env
$ vim .env
# Edit as needed
$ uvicorn main:app --reload
```

Open `http://localhost:8000/docs`
