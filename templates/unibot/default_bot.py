from django.conf import settings
from openai import OpenAI
from unicom.services.webchat.streaming import WebChatMessageStreamSink


def handle_incoming_message(message, bot, tools_list):
    streaming = message.platform == "WebChat"
    return bot.reply_using_llm(
        message,
        tools_list,
        model_default=settings.PORTACODE_LLM_MODEL,
        api_mode="responses",
        mode="chat",
        stream=streaming,
        event_sink=WebChatMessageStreamSink(message) if streaming else None,
        responses_options={"store": False, "reasoning": {"effort": settings.PORTACODE_REASONING_EFFORT}},
        openai_client=OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        ),
        system_instruction="You are a helpful assistant.",
        request=request,
    )
