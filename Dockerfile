FROM python:3.10.18
LABEL authors="jamesdev"
WORKDIR /
ENV PYTHONPATH="${PYTHONPATH}:/"
ENV SERVICE_PRINCIPAL_ID=${SERVICE_PRINCIPAL_ID}
ENV SERVICE_PRINCIPAL_PASSWORD=${SERVICE_PRINCIPAL_PASSWORD}
ENV SERVICE_PRINCIPAL_TENANT=${SERVICE_PRINCIPAL_TENANT}
COPY requirements.txt /
WORKDIR /test
COPY ./test /test
WORKDIR /app
COPY ./app /app
WORKDIR /
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN apt-get update
RUN echo msodbcsql18 msodbcsql/ACCEPT_EULA boolean true | debconf-set-selections
RUN apt-get install -y msodbcsql18
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash
RUN az login --service-principal --username $SERVICE_PRINCIPAL_ID --password $SERVICE_PRINCIPAL_PASSWORD --tenant $SERVICE_PRINCIPAL_TENANT
RUN pip install -r /requirements.txt
EXPOSE 8001
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8001"]
