def bbf_contacts(request):
    """Provide BBF contact directory to all templates"""
    contacts = [
        {'role': 'ES', 'phone': '715 773 100', 'phone_display': '0715 773 100'},
        {'role': 'AES', 'phone': '717 784 691', 'phone_display': '0717 784 691'},
        {'role': 'Chair', 'phone': '724 438 387', 'phone_display': '0724 438 387'},
        {'role': 'VC', 'phone': '723 448 590', 'phone_display': '0723 448 590'},
        {'role': 'Treasurer', 'phone': '713 660 396', 'phone_display': '0713 660 396'},
        {'role': 'AT', 'phone': '713 520 704', 'phone_display': '0713 520 704'},
        {'role': 'OS', 'phone': '724 402 029', 'phone_display': '0724 402 029'},
        {'role': 'SS', 'phone': '702 576 550', 'phone_display': '0702 576 550'},
        {'role': 'ST', 'phone': '735 213 743', 'phone_display': '0735 213 743'},
        {'role': 'SJS', 'phone': '796 089 423', 'phone_display': '0796 089 423'},
    ]
    return {'contact_list': contacts}
