FROM python:3.13-slim

# set a working directory inside the container
WORKDIR /app
# copy your code and dependency files into the image
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
#copy other files
COPY . .
# set environment variables

# define the command to run my app
CMD ["python", "main.py"]