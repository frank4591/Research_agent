#lazily loaded class
# Make get_client() a classmethod and cache the client on the class. Then other modules can call it without constructing LLMClient.

import os

from dotenv import load_dotenv
from openai import AzureOpenAI


class LLMClient:
    _client: AzureOpenAI | None = None
    model: str | None = None

    @classmethod
    def get_model(cls):
        if cls.model is not None:
            return cls.model
    

    @classmethod
    def get_client(cls) -> AzureOpenAI:
        if cls._client is None:
            load_dotenv()

            required_vars = (
                "AZURE_GPT_4o_ENDPOINT",
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_API_VERSION",
                "AZURE_OPENAI_MODEL_NAME",
            )
            missing = [name for name in required_vars if not os.getenv(name)]
            if missing:
                raise ValueError(
                    f"Missing environment variables: {', '.join(missing)}"
                )

            cls.model = os.environ["AZURE_OPENAI_MODEL_NAME"]
            cls._client = AzureOpenAI(
                azure_endpoint=os.environ["AZURE_GPT_4o_ENDPOINT"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            )

        return cls._client