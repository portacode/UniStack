from django.conf import settings
from openai import OpenAI
from unicom.services.webchat.streaming import WebChatMessageStreamSink

bot_tools = []
bot_category_is_public = True


def handle_incoming_message(message, bot, tools_list):
    streaming = message.platform == "WebChat"
    return bot.reply_using_llm(
        message=message,
        tools_list=tools_list,
        model_default=settings.PORTACODE_LLM_MODEL,
        system_instruction="You are UniStack AI. Answer clearly, directly, and helpfully.",
        mode="chat",
        openai_client=OpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
        ),
        request=request,
        api_mode="responses",
        stream=streaming,
        event_sink=WebChatMessageStreamSink(message) if streaming else None,
        responses_options={
            "store": False,
            "reasoning": {"effort": settings.PORTACODE_REASONING_EFFORT},
        },
    )
