from telegram import (
    ReplyKeyboardRemove, Update,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CallbackContext,
    ConversationHandler
)
# from cloudinary.uploader import text, upload
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail
from faunadb import query as q
from faunadb.errors import NotFound
from helpers import (
    emailcheck, dispatch_mail
)
from extensions import client
from consts import (
    CHOOSING, CLASS_STATE, BIZ_SEARCH, CHOOSE_PREF,
    SHOW_STOCKS, ADD_PRODUCTS, SME_DETAILS
)

# inital options
reply_keyboard = [
    [
        InlineKeyboardButton(
            text="SME",
            callback_data="SME"
        ),
        InlineKeyboardButton(
            text="Customer",
            callback_data="Customer"
        )
    ]
]
markup = InlineKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def start(update, context: CallbackContext) -> int:
    print("You called")
    bot = context.bot
    chat_id = update.message.chat.id
    # Check if user already exists before creating new user
    try:
        _user = client.query(
            q.get(
                q.match(
                    q.index("user_by_chat_id"),
                    chat_id
                )
            )
        )
        if _user is not None:
            bot.send_message(
                chat_id=chat_id,
                text="Hi it seems you already have an account with us!"
            )
            # figure out  what kind of user they are
            if _user['data']['is_smeowner']:
                # find business with user's chat_id
                sme = client.query(
                    q.get(
                        q.match(
                            q.index("business_by_chat_id"),
                            chat_id
                        )
                    )
                )
                if sme:
                    context.user_data["sme_name"] = sme['data']['name']
                    context.user_data['sme_cat'] = sme['data']['category']
                    context.user_data['sme_id'] = sme['ref'].id()
                    context.user_data['sme_latest'] = sme['data']['latest']
                    context.user_data['sme_link'] = sme['data']['business_link']
                    button = [
                        [
                            InlineKeyboardButton(
                                text="Add A New Product",
                                callback_data=chat_id
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="Get a business link",
                                callback_data="link"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="View your catalogue",
                                callback_data="catalogue"
                            )
                        ]
                    ]
                    _markup = InlineKeyboardMarkup(
                        button,
                        one_time_keyboard=True
                    )
                    bot.send_message(
                        chat_id=chat_id,
                        text=f"Welcome back {_user['data']['name']}!",
                        reply_markup=_markup
                    )
                    return ADD_PRODUCTS
            else:
                context.user_data["user-id"] = _user["ref"].id()
                context.user_data["user-name"] = _user['data']['name']
                context.user_data['user-data'] = _user['data']
                button = [
                    [
                        InlineKeyboardButton(
                            text="View vendors to buy from",
                            callback_data="customer"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Search for a vendor by name",
                            callback_data="customer;search"
                        )
                    ]

                ]
                bot.send_message(
                    chat_id=chat_id,
                    text=f"Welcome back {_user['data']['name']}",
                    reply_markup=InlineKeyboardMarkup(button)
                )
                return CLASS_STATE
    except NotFound:
        bot.send_message(
            chat_id=chat_id,
            text="Hi fellow, Welcome to SMEbot ,"
            "Please tell me about yourself, "
            "provide your full name, email, and phone number, "
            "separated by comma each e.g: "
            "John Doe, JohnD@gmail.com, +234567897809"
        )
        return CHOOSING


# get data generic user data from user and store
def choose(update, context):
    bot = context.bot
    chat_id = update.message.chat.id
    # create new data entry
    data = update.message.text.split(',')
    if len(data) < 3 or len(data) > 3:
        bot.send_message(
            chat_id=chat_id,
            text="Invalid entry, please make sure to input the details "
            "as requested in the instructions"
        )
        bot.send_message(
            chat_id=chat_id,
            text="Type /start, to restart bot"
        )
        return ConversationHandler.END
    new_user = client.query(
        q.do(
            # create cart
            q.create(
                q.collection("Cart"),
                {
                    "data":
                    {
                        "items": [],
                        "chat_id": chat_id
                    }
                }
            ),
            q.create(q.collection('User'), {
                "data": {
                    "name": data[0],
                    "email": data[1],
                    "telephone": data[2],
                    "is_smeowner": False,
                    "preference": "",
                    "chat_id": chat_id
                }
            })
        )
    )
    context.user_data["user-id"] = new_user["ref"].id()
    context.user_data["user-name"] = data[0]
    context.user_data['user-data'] = new_user['data']
    bot.send_message(
        chat_id=chat_id,
        text="Collected information succesfully!..🎉🎉 \n"
        "Which of the following do you identify as ?",
        reply_markup=markup
    )
    if emailcheck(data[1].replace(" ", "")):
        dispatch_mail(data[1].replace(" ", ""))
    return CLASS_STATE


def classer(update, context):
    bot = context.bot
    chat_id = update.callback_query.message.chat.id
    name = context.user_data["user-name"]
    if update.callback_query.data.lower() == "sme":
        # update user as smeowner
        client.query(
            q.update(
                q.ref(q.collection("User"), context.user_data["user-id"]),
                {"data": {"is_smeowner": True}}
            )
        )
        bot.send_message(
            chat_id=chat_id,
            text=f"Great! {name}, please tell me about your business, "
            "provide your BrandName, Brand email, Address, and phone number"
            "in that order, each separated by comma(,) each e.g: "
            "JDWears, JDWears@gmail.com, 101-Mike Avenue-Ikeja, +234567897809",
            reply_markup=ReplyKeyboardRemove()
        )

        return SME_DETAILS
    categories = [
        [
            InlineKeyboardButton(
                text="Clothing/Fashion",
                callback_data="Clothing/Fashion"
            ),
            InlineKeyboardButton(
                text="Hardware Accessories",
                callback_data="Hardware Accessories"
            )
        ],
        [
            InlineKeyboardButton(
                text="Food/Kitchen Ware",
                callback_data="Food/Kitchen Ware"
            ),
            InlineKeyboardButton(
                text="ArtnDesign",
                callback_data="ArtnDesign"
            )
        ]
    ]
    if 'search' in update.callback_query.data.lower():
        bot.send_message(
            chat_id=chat_id,
            text="Please enter the name of the business you're looking for"
        )
        return BIZ_SEARCH
    bot.send_message(
        chat_id=chat_id,
        text="Here's a list of categories available"
        "Choose one that matches your interest",
        reply_markup=InlineKeyboardMarkup(categories)
    )
    return CHOOSE_PREF


def searcher(update, context):
    bot = context.bot
    chat_id = update.message.chat.id
    data = update.message.text.lower()
    # search for business using index
    try:
        biz = client.query(
            q.get(
                q.match(
                    q.index("business_by_name"),
                    data
                )
            )
        )
        button = [
            [
                InlineKeyboardButton(
                    text="View Products",
                    callback_data=biz["data"]["name"]
                )
            ],
            [
                InlineKeyboardButton(
                    text="Select for updates",
                    callback_data="pref" + ',' + biz["data"]["name"]
                )
            ]
        ]
        if "latest" in biz['data'].keys():
            thumbnail = client.query(q.get(q.ref(q.collection("Product"), biz["data"]["latest"])))
            print(thumbnail)
            bot.send_photo(
                chat_id=chat_id,
                photo=thumbnail["data"]["image"],
                caption=f"{biz['data']['name']}",
                reply_markup=InlineKeyboardMarkup(button)
            )
        else:
            bot.send_message(
                chat_id=chat_id,
                text=f"{biz['data']['name']}",
                reply_markup=InlineKeyboardMarkup(button)
            )
        return SHOW_STOCKS
    except NotFound:
        button = [
            [
                InlineKeyboardButton(
                    text="View vendors to buy from",
                    callback_data="customer"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Search for a vendor by name",
                    callback_data="customer;search"
                )
            ]

        ]
        bot.send_message(
            chat_id=chat_id,
            text="Oops didn't find any vendor with that name"
            "check with your spelling to be sure its correct.",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return CLASS_STATE


# def update_preference(update, context):
#     bot = context.bot
#     chat_id = update.callback_query.message.chat.id
#     data = update.callback_query.data
    # if "pref" in  data:
    #     data = data.split(',')[0].replace(' ', '')
    #     print(data)
    #     user = client.query(
    #         q.update(
    #             q.ref(
    #                 q.match(q.index('user_by_name'), context.user_data['user-data']['name']),

    #             )
    #         )
    #     )
    #     # update preference
    #     client.query(
    #         q.update(
    #             q.ref(
    #                 q.collection('User'), user['ref'].id(),
    #             ),
    #             {'data': {'preference': user['data']['preference']+data+','}}
    #         )
    #     )
    # button = [
    #     [
    #         InlineKeyboardButton(
    #             text="Vieew more businesses category",
    #             callback_data='customer'
    #         )
    #     ]
    # ]
    # bot.send_message(
    #     chat_id=chat_id,
    #     text="Updated preference successfully!!"
    # )
    # return CLASS_STATE


# Control
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def search_(update, context):
    bot = context.bot
    chat_id = update.message.chat.id
    bot.send_message(
        chat_id=chat_id,
        text="Please enter the name of the business you're looking for"
    )
    return BIZ_SEARCH
