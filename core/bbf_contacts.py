from core.models import BECMember


CONTACT_DIRECTORY = (
    {"role": "ES", "title": "Executive Secretary", "phone": "0715773100", "phone_display": "0715 773 100"},
    {"role": "AES", "title": "Assistant Executive Secretary", "phone": "0717784691", "phone_display": "0717 784 691"},
    {"role": "Chair", "title": "Chairman", "phone": "0724438387", "phone_display": "0724 438 387"},
    {"role": "VC", "title": "Vice Chairman", "phone": "0723448590", "phone_display": "0723 448 590"},
    {"role": "Treasurer", "title": "Treasurer", "phone": "0713660396", "phone_display": "0713 660 396"},
    {"role": "AT", "title": "Assistant Treasurer", "phone": "0713520704", "phone_display": "0713 520 704"},
    {"role": "OS", "title": "Organising Secretary", "phone": "0724402029", "phone_display": "0724 402 029"},
    {"role": "SS", "title": "Secretary Secondary", "phone": "0702576550", "phone_display": "0702 576 550"},
    {"role": "ST", "title": "Secretary Tertiary", "phone": "0735213743", "phone_display": "0735 213 743"},
    {"role": "SJS", "title": "Secretary JSS", "phone": "0796089423", "phone_display": "0796 089 423"},
)

TITLE_ALIASES = {
    "Assistant Executive Secretary": {"Assistant ES"},
}


def _build_bec_lookup():
    lookup = {}
    for member in BECMember.objects.all():
        normalized = member.title.strip().lower()
        lookup[normalized] = member

    for title, aliases in TITLE_ALIASES.items():
        primary = lookup.get(title.lower())
        if primary:
            continue
        for alias in aliases:
            alias_match = lookup.get(alias.lower())
            if alias_match:
                lookup[title.lower()] = alias_match
                break

    return lookup


def get_bbf_contacts():
    bec_lookup = _build_bec_lookup()
    contacts = []

    for contact in CONTACT_DIRECTORY:
        bec_member = bec_lookup.get(contact["title"].lower())
        local_phone = contact["phone"]
        tel_phone = local_phone[1:] if local_phone.startswith("0") else local_phone
        contacts.append(
            {
                **contact,
                "holder_name": bec_member.name if bec_member else "",
                "tel_phone": tel_phone,
            }
        )

    return contacts
