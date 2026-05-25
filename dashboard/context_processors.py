from core.bbf_contacts import get_bbf_contacts


def bbf_contacts(request):
    """Provide BBF contact directory to all templates"""
    return {"contact_list": get_bbf_contacts()}
