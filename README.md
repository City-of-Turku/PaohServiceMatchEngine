# PaohServiceMatchEngine

# Introduction 

This repository is for Service Matcher and its underlying services: NLP Vectorizer, Lexical Text Search and Service Data Processor.
-   The Service Matcher provides an API to get service recommendations from the underlying service data based on natural language text and other parameters.
-   NLP Vectorizer is a simple service which only vectorizes text using a NLP model and provides an API for the text vectorization.
-   Lexical Text Search is a service which can search services bases on text query using classical lexical algorithms like BM25.
-   Service Data Processor is an Azure Function which is triggered periodically to fetch service data from Mongo and to process it for the Service Matcher's needs (atm only creates service text vectors using the NLP Vectorizer and translates missing service description translations using Azure Translator). 

These services can be deployed locally or to the Azure cloud as Docker containers.

# Deploying to Azure cloud:

Docker images are deployed to the test and production environments from `dev` and `main` branches respectively. The pipeline uses Azure Container registry to store created images and later deploys them to run as containers in AKS cluster under Private Network in Azure. The connection credentials are a part of the pipeline and those are fetched from Azure Key Vault as part of the pipeline.

To run the deployment it is enough to merge to `dev` and `main` branches after which tests are run and if those succeed the new version is deployed.

The Azure Devops pipeline is defined in `azure-pipelines.yml` file and AKS Kubernetes configs are in `kube/` folder.

# Development locally

You need Docker, MongoDB and Azure Functions Core Tools installed on your host machine to run all three services locally. To install Azure Functions Core tools, check Azure's [documentation](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=windows%2Ccsharp%2Cbash#install-the-azure-functions-core-tools)

NLP Vectorizer uses Python NLP library called [Sentence-Transformers](https://www.sbert.net/docs/) and one ready pretrained NLP model called `paraphrase-multilingual-mpnet-base-v2` to vectorize text. The model is quite large (about 1GB) and because Azure Repos with Git LFS (large files) enabled cannot work with Git SSH connection anymore, the model won't be stored in this repo. At the first startup of the NLP Vectorizer service, the docker container will create new directory called `nlp_models` where it will automatically download the NLP model if it odesn't exist there yet.

To run Service Matcher, NLP Vectorizer and Lexical Text Search:
1. Set up a MongoDB to run on your host machine in port 27017 or use external MongoDB server, Mongo must have database `service_db` with collection `services`. You can also use Mongo container from `mongo` directory in this repository. If you use that, remember to set Mongo password and username to the `mongo/docker-compose.yml` file.
2. If you decide to run Mongo locally **without the predefined mongo container** (outside container mentioned in the previous step) allow access from external IPs to MongoDB by editing Mongo configuration file, by default you cannot access MongoDB from any other IP but the host
3. Add your Mongo host, username and password to `docker-compose.yml` file under repository root, not the one under `mongo`. If you used the Mongo container, use the same credentials.
4. Run `docker-compose up -d --build` to build images and launch containers, rerun to build it again when needed.
5. Service Matcher API is now available at  [localhost:80](localhost:80)
6. Service Matcher API automatic documentation is now available at [localhost:80/docs](localhost:80/docs)

To run Service Data Processor:
1. Run `cd service_data_processor_app` to go to Service Data Processor directory
2. Create Python virtual environment by running `python3 -m venv <name_of_virtualenv>`
3. Activate the virtual environment by running `<name_of_virtualenv>\scripts\activate` on Windows or `source <name_of_virtualenv>/bin/activate` on Linux/Mac
4. Install needed Python libraries into your virtual environemnt by running `pip3 install -r requirements.txt`
5. Add your Mongo connection info to `local.settings.json` file. This file is only used to test the function locally. **DO NOT PUSH THIS FILE INTO REPO AFTER ADDING YOUR DETAILS**
6. Add Azure Storage Account name and key to the same `local.settings.json` file. This is needed for function to work. You can use the Storage Account that is available in Azure test environment. **DO NOT PUSH THIS FILE INTO REPO AFTER ADDING YOUR DETAILS**
7. To make sure you won't push your updated `local.settings.json` file into repo, run `git update-index --assume-unchanged local.settings.json`
8. Run `func start --python --verbose` to start the Azure Function (Service Data Processor) locally. Function should run locally as it would do in AKS.
