FROM python:3

WORKDIR /usr/src/app

# updates and prereqs
RUN apt-get update
RUN apt-get install -y gdal-bin python3-gdal
RUN apt-get install -y python3-pip 

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip3 install --upgrade pip
COPY ./requirements.txt /usr/src/app
RUN pip3 install -r requirements.txt

# copy project
COPY . /usr/src/app

# get ready to run project
WORKDIR /usr/src/app/cityhall
RUN python3 manage.py collectstatic --noinput

CMD bash -c "python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8000 --insecure"
