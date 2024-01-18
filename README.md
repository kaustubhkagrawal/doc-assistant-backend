This is a [LlamaIndex](https://www.llamaindex.ai/) project using [FastAPI](https://fastapi.tiangolo.com/) bootstrapped with [`create-llama`](https://github.com/run-llama/LlamaIndexTS/tree/main/packages/create-llama). Aiming to do RAG on documents

## Getting Started

First, setup the environment:

```
poetry shell
poetry install

cp example.env .env

# Load env variables
set -a
source .env
```

By default, we use the OpenAI LLM (though you can customize, see app/api/routers/chat.py). As a result you need to specify an `OPENAI_API_KEY` in an .env file in this directory.

Example `.env` file:

```
OPENAI_API_KEY=<openai_api_key>
```

Second, generate the embeddings of the documents in the `./data` directory (if this folder exists - otherwise, skip this step):

```
pip install awscli awscli-local
# Setup for localstack
make setup_localstack

# DB Migrate
make migrate
```

Third, run the development server:

```
poetry run start 
# Start postgres and localstack using docker.
make run
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) with your browser to see the Swagger UI of the API.

The API allows CORS for all origins to simplify development. You can change this behavior by setting the `ENVIRONMENT` environment variable to `prod`:

```
ENVIRONMENT=prod uvicorn main:app
```

## Learn More

To learn more about LlamaIndex, take a look at the following resources:

- [LlamaIndex Documentation](https://docs.llamaindex.ai) - learn about LlamaIndex.

You can check out [the LlamaIndex GitHub repository](https://github.com/run-llama/llama_index) - your feedback and contributions are welcome!
