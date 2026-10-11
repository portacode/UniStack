"""Project-owned instructions shared by the native chat UI and HTTP API.

Extend this function for document retrieval or other product context. `request`
is the persisted UniCom Request, not Django's HTTP request. Authorize all data
against the persisted account/message owner before including it. Keep source
material clearly delimited and treat its contents as data, never instructions.
"""
from core.branding import get_brand


def build_system_instruction(message, request=None):
    return f"You are {get_brand()['name']}'s assistant. Answer clearly, directly, and helpfully."
