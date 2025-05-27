from llm import LLMService

llm_service = LLMService(
        config_path=".env",
        temperature=0,
        gpt_version="gpt-4.1-mini"
    )
messages = [
                ("user", "hi, how are you?")
        ]
result = llm_service.send_message(messages)
print(result)
