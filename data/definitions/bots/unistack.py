from core.integrations.bot import reply

bot_tools = []
bot_category_is_public = True


def handle_incoming_message(message, bot, tools_list):
    return reply(message, bot, tools_list, request=request)
