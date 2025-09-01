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
RUN curl -sSL -O https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb
RUN rm packages-microsoft-prod.deb
RUN apt-get update
RUN echo msodbcsql18 msodbcsql/ACCEPT_EULA boolean true | debconf-set-selections
RUN apt-get install -y msodbcsql18
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash
RUN az login --service-principal --username $SERVICE_PRINCIPAL_ID --password $SERVICE_PRINCIPAL_PASSWORD --tenant $SERVICE_PRINCIPAL_TENANT
RUN pip install -r /requirements.txt
EXPOSE 8000
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]