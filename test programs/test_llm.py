from llm import LLMService

llm_service = LLMService(
        config_path=".env",
        openai_api_version="2024-12-01-preview",
        azure_deployment="gpt-4o-mini",
        temperature=0
    )
messages = [
                ("user", "hi, how are you?")
        ]
result = llm_service.send_message(messages)
print(result)
