## Introduction

This is the backend API for subscribers to add/remove themselves
from the flood services mailing list. The mailing list contains
subscriber email addresses and postcodes associated with that address.

## Prerequisites

### Python

Python 3 is necessary for this program to run. The latest version of python can be found [here](https://www.python.org/downloads/).

You also need pip, which should be installed by default. If, for some reason it isn't, you can install it with the following command:

python `get-pip.py`


### Database Instances
There are 2 databases - one SQL instance containing a table with email addresses joined to another table containing postcodes, and one CosmosDB instance containing a complete list of all England postcodes and their associated geojson geometries - which make this whole thing go.

I am absolutely not willing to share either of these endpoints, and I'm certainly not sharing any credentials. Therefore, it would be remiss of me not to be completely blunt and tell you that attempts to get this producer to run on your own machine are fairly unlikely since you would need to create your own SQL/NoSQL instances yourself and either copy the existing schema exactly, or re-engineer the code to fit the schema you choose to use.

You would also have to shard, partition and populate these databases yourselves. If you decide to use CosmosDB, as I did, you shall need a Microsoft Azure account, and shall also have to grant RBAC to the application using data plane. A guide on this is available on [learn.microsoft](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/how-to-grant-data-plane-access?tabs=built-in-definition%2Ccsharp&pivots=azure-interface-cli)

Once you've done that, you would need to populate your SQL instance with dummy emails and postcodes.

You would also need to populate the NoSQL database with postcode and geojson geometry data, breaking it down into area, district, and full postcode. The dataset I used to do this can be found [here](https://longair.net/blog/2021/08/23/open-data-gb-postcode-unit-boundaries/)...good luck!

If you've not turned tail and fled by now, I'm sorry...but, once you've got all this horrid preamble out of the way, you can go ahead and copy/paste your database connection strings and relevant database suffixes into the .env_template file


### Environment variables
If you have followed all the previous steps, all you have to do now is remove the _template portion of the .env_template file to give you your .env file which shall be referenced at runtime.

## Installation
### Virtual environment
While this step is not strictly necessary, it is recommended.

Once you have cloned/forked the repository, in the root directory create a python virtual environment with this command:

#### Linux/macOS
`python3 -m venv <your-virtual-environment>`

#### Windows
`py -m venv <your-virtual-environment>`

and then activate it:

#### Linux/macOS
`source <your-virtual-environment>/bin/activate`

#### Windows
`<your-virtual-environment>\Scripts\activate`

### Install dependencies
Once you have created and activated your virtual environment (or if you want to install dependencies directly to your python directory) run the following command to install all dependencies:

#### Linux/macOS
`python3 pip install -r requirements.txt`

#### Windows
`py -m pip install -r requirements.txt`

## Run the script
Once all dependencies are installed, and your databases are online, ensure your instance of rabbitMQ is running (as well as your instance of redis) and then run the script with:

#### Linux/macOS
`python3 ./app/main.py`

#### Windows
`py ./app/main.py`

By default, the API will run on `localhost:8000`

You can test the endpoints either in your browser, if using an API endpoint testing suite like postman.


## Usage

Endpoints are exposed in the `routes` directory:

```
├── app
│   ├── routes
│   │   └── subscribers.py

```

### Subscribers

#### Return All Subscribers

`localhost:8000//subscribers/all`

GET method

Returns JSON

Hitting this endpoint will return a list of every subscriber and their associated postcodes
from the database.

Returns a 500 status code if the database cannot be reached.

#### Return Subscriber by ID

`localhost:8000//subscribers/get/id/<subscriber-id>`

GET method

Returns JSON

Returns the subscriber with the provided ID from the database.

Returns a 404 status code if no subscriber with the given ID exists.

Returns a 500 status code the database cannot be reached.

#### Return Subscriber by Email

`localhost:8000//subscribers/get/email/<subscriber-id>`

GET method

Returns JSON

Returns the subscriber with the provided email from the database.

Returns a 404 status code if no subscriber with the given email exists.

Returns a 500 status code the database cannot be reached.

#### Add New Subscriber

`localhost:8000//subscribers/add/`

POST method

Accepts x-www-form-urlencoded

Returns JSON

Form structure:

```bash
email: <subscriber-email>
postcodes:[<postcode-A>, <postcode-B>, ...]
```
Returns a 201 status code upon successful adding of a subscriber to the database.

Returns a 204 if one or more of the provided postcodes are not covered by the flood monitoring service.

Returns a 409 status code if the provided email address already belongs to a subscriber.


#### Delete Subscriber by ID

`localhost:8000//subscribers/delete/<subscriber-id>`

DELETE method

Returns JSON

Returns a 204 status code if the subscriber with the associated ID was deleted successfully.

Returns a 404 status code if no subscriber with the provided ID could be found.

