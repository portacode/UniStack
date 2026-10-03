from core.integrations.bot import reply


def handle_incoming_message(message, bot, tools_list):
    return reply(message, bot, tools_list, request=request)
