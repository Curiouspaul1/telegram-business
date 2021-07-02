from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove, Update,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CommandHandler, CallbackContext,
    ConversationHandler, MessageHandler,
    Filters, Updater, CallbackQueryHandler
)
from config import (
    api_key, sender_email,
    api_secret,
    FAUNA_KEY
)
import cloudinary
from cloudinary.uploader import upload
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from faunadb import query as q
from faunadb.client import FaunaClient
from faunadb.errors import NotFound
from helpers import emailcheck
import os



# configure cloudinary
cloudinary.config(
    cloud_name="curiouspaul",
    api_key=api_key,
    api_secret=api_secret
)

# fauna client config
client = FaunaClient(secret=FAUNA_KEY)

# Define Options
CHOOSING, CLASS_STATE, SME_DETAILS, CHOOSE_PREF, \
    SME_CAT, ADD_PRODUCTS, SHOW_STOCKS, POST_VIEW_PRODUCTS = range(8)

# inital options

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
        if _user != None:
            print(_user)
            bot.send_message(
                chat_id=chat_id,
                text="Hi it seems you already have an account with us!"
            )
            # figure out  what kind of user they are
            if _user['data']['is_smeowner']:
                print("yes")
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
                    button = [
                        [
                            InlineKeyboardButton(
                                text="Add A New Product",
                                callback_data=chat_id
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
                            text="View businesses to buy from",
                            callback_data="customer"
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
            text= "Hi fellow, Welcome to SMEbot ,"
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
        q.create(q.collection('User'), {
            "data":{
                "name":data[0],
                "email":data[1],
                "telephone":data[2],
                "is_smeowner":False,
                "preference": "",
                "chat_id":chat_id
            }
        })
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
    # print(data[1].replace(" ",""))
    # print(emailcheck(data[1].replace(" ","")))
    if emailcheck(data[1].replace(" ","")):
        dispatch_mail(data[1].replace(" ",""))
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
                {"data": {"is_smeowner":True}}
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
    bot.send_message(
        chat_id=chat_id,
        text="Here's a list of categories available"
        "Choose one that matches your interest",
        reply_markup=InlineKeyboardMarkup(categories)
    )
    return CHOOSE_PREF

def business_details(update, context):
    bot = context.bot
    chat_id = update.message.chat.id
    data = update.message.text.split(',')
    if len(data) < 4 or len(data) > 4:
        bot.send_message(
            chat_id=chat_id,
            text="Invalid entry, please make sure to input the details "
            "as requested in the instructions"
        )
        return SME_DETAILS
    context.user_data["sme_dets"] = data
    # categories = [
    #         ['Clothing/Fashion', 'Hardware Accessories'],
    #         ['Food/Kitchen Ware', 'ArtnDesign'],
    #         ['Other']
    # ]
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
    markup = InlineKeyboardMarkup(categories, one_time_keyboard=True)
    bot.send_message(
        chat_id=chat_id,
        text="Pick a category for your business from the options",
        reply_markup=markup
    )
    return SME_CAT

def business_details_update(update, context):
    bot = context.bot
    chat_id = update.callback_query.message.chat.id
    choice = update.callback_query.data
    user_id = context.user_data['user-id']
    # create business
    new_sme = client.query(
        q.create(
            q.collection("Business"),
            {"data":{
                "name":context.user_data["sme_dets"][0],
                "email":context.user_data["sme_dets"][1],
                "address":context.user_data["sme_dets"][2],
                "telephone":context.user_data["sme_dets"][3],
                "category":choice.lower(),
                "chat_id": chat_id
            }}
        )
    )
    context.user_data["sme_name"] = context.user_data["sme_dets"][0]
    context.user_data["sme_id"] = new_sme["ref"].id()
    context.user_data["sme_cat"] = choice
    button = [[
        InlineKeyboardButton(
            text="Add a product",
            callback_data=choice.lower()
        )
    ]]
    bot.send_message(
        chat_id=chat_id,
        text="Business account created successfully, "
        "let's add some products shall we!.",
        reply_markup=InlineKeyboardMarkup(button)
    )
    return ADD_PRODUCTS

def add_product(update, context):
    bot = context.bot
    chat_id = update.callback_query.message.chat.id
    bot.send_message(
        chat_id=chat_id,
        text="Add the Name, Description, and Price of product, "
        "separated by commas(,) as caption to the product's image"
    )
    return ADD_PRODUCTS

def product_info(update: Update, context: CallbackContext):
    data = update.message
    bot = context.bot
    photo = bot.getFile(update.message.photo[-1].file_id)
    file_ = open('product_image', 'wb')
    photo.download(out=file_)
    data = update.message.caption.split(',')
    # upload image to cloudinary
    send_photo = upload('product_image', width=200, height=150, crop='thumb')
    # create new product
    newprod = client.query(
        q.create(
            q.collection("Product"),
            {"data": {
                    "name":data[0],
                    "description":data[1],
                    "price":float(data[2]),
                    "image":send_photo["secure_url"],
                    "sme":context.user_data["sme_name"],
                    "sme_chat_id": update.message.chat.id,
                    "category":context.user_data["sme_cat"]
                }
            }
        )
    )
    # add new product as latest
    client.query(
        q.update(
            q.ref(q.collection("Business"), context.user_data["sme_id"]),
            {"data": {
                "latest": newprod["ref"].id()
            }}
        )
    )
    # context.user_data["product_data"] = newprod['data']
    button = [[InlineKeyboardButton(
        text='Add another product',
        callback_data=context.user_data["sme_name"]
    )]]
    update.message.reply_text(
        "Added product successfully",
        reply_markup=InlineKeyboardMarkup(button)
    )
    return ADD_PRODUCTS

## CUSTOMER
def customer_pref(update, context):
    bot = context.bot
    chat_id = update.callback_query.message.chat.id
    data = update.callback_query.data
    print(data)
    # get all businesses in category
    try:
        smes_ = client.query(
            q.map_(
                lambda var: q.get(var),
                q.paginate(
                    q.match(
                        q.index("business_by_category"),
                        str(data).lower()
                    )
                )
            )
        )
        print(smes_)
        for sme in smes_["data"]:
            button = [
                [
                    InlineKeyboardButton(
                        text="View Products",
                        callback_data=sme["data"]["name"]
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Select for updates",
                        callback_data="pref"+','+sme["data"]["name"]
                    )
                ]
            ]
            if "latest" in sme['data'].keys():
                thumbnail = client.query(q.get(q.ref(q.collection("Product"), sme["data"]["latest"])))
                print(thumbnail)
                bot.send_photo(
                    chat_id=chat_id,
                    photo=thumbnail["data"]["image"],
                    caption=f"{sme['data']['name']}",
                    reply_markup=InlineKeyboardMarkup(button)
                )
            else:
                bot.send_message(
                    chat_id=chat_id,
                    text=f"{sme['data']['name']}",
                    reply_markup=InlineKeyboardMarkup(button)
                )
        return SHOW_STOCKS
    except NotFound:
        button = [[
            InlineKeyboardButton(
                text="Select another Category?",
                callback_data="customer"
            )
        ]]
        bot.send_message(
            chat_id=chat_id,
            text="Nothing here yet",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return CLASS_STATE
    # return SHOW_STOCKS

def show_products(update, context):
    bot = context.bot
    chat_id = update.callback_query.message.chat.id
    data = update.callback_query.data
    if "pref" in  data:
        data = data.split(',')[0]
        print(data.split(','))
        print(data)
        print(data.replace(' ', ''))
        user = client.query(
            q.get(
                q.ref(
                    q.match(q.index('user_by_name'), context.user_data['user-data']['name']),

                )
            )
        )
        # update preference
        client.query(
            q.update(
                q.ref(
                    q.collection('User'), user['ref'].id()
                ),
                {'data': {'preference': user['data']['preference']+data+','}}
            )
        )
        button = [
            [
                InlineKeyboardButton(
                    text="View more businesses category",
                    callback_data='customer'
                )
            ]
        ]
        bot.send_message(
            chat_id=chat_id,
            text="Updated preference successfully!!"
        )
        return CLASS_STATE
    products = client.query(
        q.map_(
            lambda x: q.get(x),
            q.paginate(
                q.match(
                    q.index("product_by_business"),
                    update.callback_query.data
                )
            )
        )
    )

    if len(products['data']) == 0:
        button = [
            [
                InlineKeyboardButton(
                    text="View businesses to buy from",
                    callback_data="customer"
                )
            ]
        ]
        bot.send_message(
            chat_id=chat_id,
            text="'Nothing here yet, user hasn't added any products!, check back later",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return CLASS_STATE
    for product in products["data"]:
        context.user_data["sme_id"] = product['data']['sme']
        button = [
            [
                InlineKeyboardButton(
                    text="Send Order",
                    callback_data="order;" + product["ref"].id()
                )
            ],
            [
                InlineKeyboardButton(
                    text="Contact business owner",
                    callback_data="contact;" + product["data"]["sme"]
                )
            ]
        ]
        bot.send_photo(
            chat_id=chat_id,
            photo=product["data"]["image"],
            caption=f"{product['data']['name']} \nDescription: {product['data']['description']}\nPrice:{product['data']['price']}",
            reply_markup=InlineKeyboardMarkup(button)
        )
    return POST_VIEW_PRODUCTS


def post_view_products(update, context):
    bot = context.bot
    chat_id = update.callback_query.message.chat.id
    data = update.callback_query.data
    if "order" in data:
        product = client.query(
        q.get(
            q.ref(
                    q.collection("Product"),
                    data.split(';')[1]
                )
            )
        )["data"]
        bot.send_message(
            chat_id=product['sme_chat_id'],
            text="Hey you have a new order"
        )
        bot.send_photo(
            chat_id=product['sme_chat_id'],
            caption=f"Name: {product['name']}\n\nDescription: {product['description']}\n\nPrice: {product['price']}"
            f"\n\n Customer's Name: {context.user_data['user-name']}",
            photo=product['image']
        )  
        bot.send_contact(
            chat_id=product['sme_chat_id'],
            phone_number=context.user_data['user-data']['telephone'],
            first_name=context.user_data['user-data']['name']
        )
        bot.send_message(
            chat_id=chat_id,
            text="Placed order successfully"
        )
    elif 'contact' in data:
        sme_ = client.query(
            q.get( 
                q.match(
                    q.index("business_by_name"), 
                    data.split(';')[1]
                )
            )
        )['data']
        bot.send_message(
            chat_id=chat_id,
            text=f"Name: {sme_['name']}\n\nTelephone: {sme_['telephone']}\n\nEmail:{sme_['email']}"
        )

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