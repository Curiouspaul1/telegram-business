import re

# Email regex

def emailcheck(str):
    """
        emailCheck uses regex via python3's re module to verify
        that received argument is indeed an email address.
        -------
        type(argument) == <str_class>
        type(return) == <bool_class>
        emailcheck can also find an email address from within any
        string text, returns False if it finds none.
    """

    emailreg = re.compile(r'''
        # username
        ([a-zA-Z0-9_\-+%]+|[a-zA-Z0-9\-_%+]+(.\.))
        # @ symbol
        [@]
        # domain name
        [a-zA-Z0-9.-]+
        # dot_something
		[\.]
        ([a-zA-Z]{2,4})
    ''',re.VERBOSE)
    try:
        if emailreg.search(str):
            return True
        else:
            return False
    except AttributeError:
        raise False

