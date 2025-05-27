import os, toml
from langchain_openai import AzureChatOpenAI
from langchain_core.output_parsers import *
from langchain_core.prompts import ChatPromptTemplate

class LLMService:
    # constructor
    def __init__(self, config_path=".env",
                temperature = 0, streaming = False, json_mode = False, 
                gpt_version = "gpt-4o-mini"):
        # Try to load the API key and endpoint from the configuration file
        try:
            config = toml.load(config_path)
            if gpt_version == "gpt-4o-mini":
                # Set the environment variables for the Azure OpenAI endpoint and API key
                openai_api_version="2024-12-01-preview"
                azure_deployment="gpt-4o-mini"
                os.environ["AZURE_OPENAI_ENDPOINT"] = config["AZURE_OPENAI"]["AZURE_OPENAI_ENDPOINT"]
                os.environ["AZURE_OPENAI_API_KEY"] = config["AZURE_OPENAI"]["AZURE_OPENAI_API_KEY"]
            elif gpt_version == "gpt-4.1-mini":
                openai_api_version="2024-12-01-preview"
                azure_deployment="gpt-4.1-mini"                
                os.environ["AZURE_OPENAI_ENDPOINT"] = config["AZURE_OPENAI"]["AZURE_OPENAI_ENDPOINT_41"]
                os.environ["AZURE_OPENAI_API_KEY"] = config["AZURE_OPENAI"]["AZURE_OPENAI_API_KEY_41"]
        except (FileNotFoundError, toml.TomlDecodeError):
            # Try to load config from Streamlit secrets if available
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and "AZURE_OPENAI" in st.secrets:
                    if gpt_version == "gpt-4o-mini":
                        # Set the environment variables for the Azure OpenAI endpoint and API key
                        openai_api_version="2024-12-01-preview"
                        azure_deployment="gpt-4o-mini"
                        os.environ["AZURE_OPENAI_ENDPOINT"] = config["AZURE_OPENAI"]["AZURE_OPENAI_ENDPOINT"]
                        os.environ["AZURE_OPENAI_API_KEY"] = config["AZURE_OPENAI"]["AZURE_OPENAI_API_KEY"]
                    elif gpt_version == "gpt-4.1-mini":
                        openai_api_version="2024-12-01-preview"
                        azure_deployment="gpt-4.1-mini"                
                        os.environ["AZURE_OPENAI_ENDPOINT"] = config["AZURE_OPENAI"]["AZURE_OPENAI_ENDPOINT_41"]
                        os.environ["AZURE_OPENAI_API_KEY"] = config["AZURE_OPENAI"]["AZURE_OPENAI_API_KEY_41"]
                else:
                    raise ImportError("Streamlit secrets not configured with AZURE_OPENAI credentials")
            except ImportError as e:
                raise ValueError(f"Configuration not found. Either provide a valid config file or run in a Streamlit environment with proper secrets configuration. Error: {str(e)}")

        model_kwargs = {}
        if json_mode:
            model_kwargs = {"response_format": {"type": "json_object"}}
                    
        # Initialize the AzureChatOpenAI instance
        self.llm = AzureChatOpenAI(
            openai_api_version = openai_api_version,
            azure_deployment = azure_deployment,
            temperature = temperature,
            streaming = streaming,
            model_kwargs = model_kwargs
        )
    
    def getLLM(self):
        return self.llm
    
    def send_message(self, messages):
        prompt_template = ChatPromptTemplate.from_messages(messages) 
        chain = prompt_template| self.llm | StrOutputParser() #JsonOutputParser()
        output = chain.invoke({})
        return output

# if main program, run the LLM
if __name__ == "__main__":    
    llm = LLMService()
    result=llm.send_message(["Hello, how are you?"])
    print(result)
