FROM python:3
LABEL Simon Carr
COPY ./requirements.txt /requirements.txt
WORKDIR /
RUN pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
COPY . /
ENTRYPOINT [ "python3" ]
CMD [ "processJobs.py" ]
