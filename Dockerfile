FROM python:3.8

RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev

# Set GDAL_LIBRARY_PATH
ENV GDAL_LIBRARY_PATH /usr/lib/libgdal.so

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /medaram_analytics

COPY requirements.txt /medaram_analytics/

RUN pip install -r requirements.txt

COPY . /medaram_analytics/

EXPOSE 8000

RUN python manage.py 

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "medaram_analytics.wsgi:application"]
