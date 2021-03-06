# flake8: noqa

from hashlib import new
import re
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import os
from extensions import client
from faunadb import query as q

load_dotenv()


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


# emailing function
def dispatch_mail(email):
    print(email)
    with open('email.html', 'r', encoding="utf8") as file:
        msg = Mail(
            from_email=(os.getenv('SENDER_EMAIL'), 'Paul From Telegram-Business'),
            to_emails=[email],
            subject="Welcome to smebot! - Next Steps",
            html_content=file.read()
        )
    try:
        client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY')).send(msg)
        print(client.status_code)
        print("Done!..")
    except Exception as e:
        print(e.message)


# generate unique business link
def generate_link(biz_name):
    url_ = "https://rdre.me/tgbiz"
    return f"{url_}/{biz_name}"


# parse product update details
def parse_product_info(data:str):
    dic_ = {}
    parsed_ = data.replace('}','')
    parsed_ = parsed_.replace('{','')
    parsed_ = parsed_.split(',')
    print(parsed_)
    for item in parsed_:
        if len(item.split(':')) == 2:
            data_ = item.split(':')
            print(data_)
            dic_[data_[0]] = data_[1]
        else:
            return False
    return dic_


# update biz latest product
def update_sme_latest(biz_name):
    client.query(
        q.do(
            q.let(
                {
                    'biz_stack': q.if_(
                        q.is_empty(
                            q.match(
                                q.index("business-stack_by_name"),
                                biz_name
                            )
                        ),
                        q.create(
                            q.collection('Business_Stack'),
                            {
                                'data': {
                                    'name': biz_name,
                                    'stack': []
                                }
                            }
                        ),
                        q.get(
                            q.match(
                                q.index("business-stack_by_name"),
                                biz_name
                            )
                        )
                    )
                },
                q.let(
                    {
                        'revr_stack': q.reverse(q.select(['data', 'stack'], q.var('biz_stack')))
                    },
                    q.update(
                        # fetch sme and update the latest product
                        q.select(
                            ['ref'],
                            q.get(
                                q.match(
                                    q.index('business_by_name'),
                                    biz_name
                                )
                            )
                        ),
                        {
                            'data': {
                                'latest': q.select(
                                    [0],
                                    q.var('revr_stack')
                                )
                            }
                        }
                    )
                )
            )
        )
    )
