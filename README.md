python manage.py migrate
python manage.py seed_members --file Members.docx --credentials-file member_seed_credentials.csv

LOGIN FLOW
 login now uses TSC number + password

The temporary password format is FirstGivenName@Last4Digits, so Mr Andiwo, Bernard Omondi with 785893 becomes Bernard@5893.