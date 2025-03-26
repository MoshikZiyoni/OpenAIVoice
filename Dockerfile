# Use the official Python image as the base image
FROM python:3.10.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# # Install system dependencies
# RUN apt-get update \
#     && apt-get install -y \
#         autoconf \
#         automake \
#         build-essential \
#         ca-certificates \
#         g++ \
#         git \
#         libtool \
#         libleptonica-dev \
#         pkg-config \
#         libtiff5-dev \
#         zlib1g-dev \
#     && apt-get clean



# Install Python dependencies (this step will be cached if requirements.txt doesn't change)
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

# Set the working directory in the container
WORKDIR /code

# Copy the Django project files to the working directory
COPY ./callAPI /code/callAPI
COPY ./OpenAIVoice /code/OpenAIVoice
COPY ./manage.py /code/
# COPY build.sh /code/

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose the port on which your Django app will run
EXPOSE 8000

# Run the Django app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

