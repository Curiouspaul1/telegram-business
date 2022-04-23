from faunadb.errors import FaunaError
from faunadb import query as q
from helpers import generate_link, parse_product_info
from extensions import client
from consts import (
    SME_DETAILS, SME_CAT, SME_CATALOGUE,
    ADD_PRODUCTS, POST_VIEW_CATALOGUE
)
from telegram import (
    Update,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CallbackContext,
    ConversationHandler
)
from cloudinary.uploader import upload
from helpers import update_sme_latest


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
    biz_link = generate_link(context.user_data["sme_dets"][0])
    # create business
    new_sme = client.query(
        q.create(
            q.collection("Business"),
            {"data": {
                "name": context.user_data["sme_dets"][0].lower(),
                "email": context.user_data["sme_dets"][1],
                "address": context.user_data["sme_dets"][2],
                "telephone": context.user_data["sme_dets"][3],
                "category": choice.lower(),
                "business_link": biz_link,
                "chat_id": chat_id
            }}
        )
    )
    context.user_data["sme_name"] = context.user_data["sme_dets"][0]
    context.user_data["sme_id"] = new_sme["ref"].id()
    context.user_data["sme_cat"] = choice
    context.user_data["sme_link"] = biz_link
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
    if "link" in update.callback_query.data:
        bot.send_message(
            chat_id=chat_id,
            text=context.user_data['sme_link']
        )
        bot.send_message(
            chat_id=chat_id,
            text="Here you go!, share the link with people so they can see your store."
        )
        return ConversationHandler.END
    elif "catalogue" in update.callback_query.data:
        context.user_data['sme_chat_id'] = chat_id
        return SME_CATALOGUE
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
    file_ = open('product_image.png', 'wb')
    photo.download(out=file_)
    data = update.message.caption.split(',')
    # upload image to cloudinary
    with open('product_image.png', 'rb') as file_:
        send_photo = upload(
            file_,
            width=200, height=150,
            crop='thumb'
        )
        # create new product
        newprod = client.query(
            q.create(
                q.collection("Product"),
                {
                    "data":
                    {
                        "name": data[0],
                        "description": data[1],
                        "price": float(data[2]),
                        "image": send_photo["secure_url"],
                        "sme": context.user_data["sme_name"],
                        "sme_chat_id": update.message.chat.id,
                        "category": context.user_data["sme_cat"]
                    }
                }
            )
        )
        # update latest products stack
        client.query(
            q.let(
                {
                    "biz_stack": q.if_(
                        q.is_empty(
                            q.match(
                                q.index("business-stack_by_name"),
                                context.user_data["sme_name"]
                            )
                        ),
                        q.create(
                            q.collection('Business_Stack'),
                            {
                                'data': {
                                    'name': context.user_data['sme_name'],
                                    'stack': []
                                }
                            }
                        ),
                        q.get(
                            q.match(
                                q.index("business-stack_by_name"),
                                context.user_data["sme_name"]
                            )
                        )
                    )
                },
                q.update(
                    q.select(['ref'], q.var('biz_stack')),
                    {
                        "data": {
                            'stack': q.append(
                                newprod['ref'].id(),
                                q.select(
                                    ['data', 'stack'],
                                    q.var('biz_stack')
                                )
                            )
                        }
                    }
                )
            )
        )
        # update latest on business using stack
        update_sme_latest(context.user_data['sme_name'])

        # create response
        button = [[InlineKeyboardButton(
            text='Add another product',
            callback_data=context.user_data["sme_name"]
        )]]
        update.message.reply_text(
            "Added product successfully",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return ADD_PRODUCTS


def post_show_catalogue(update, context):
    bot = context.bot
    chat_id = update.callback_query.message.chat.id
    # check for selected option
    data = update.callback_query.data
    if "Edit" in data:
        bot.send_message(
            chat_id=chat_id,
            text="Kindly add details for the update using the following format, "
            "{product_attribute: value} for example {price: 50} or perhaps, "
            "{price: 50, description: new description}"
        )
        context.user_data['product_id'] = data.split(';')[1]
        return POST_VIEW_CATALOGUE
    # else if user chooses to remove product
    # faunadb transaction to delete product and
    # update biz latest product
    client.query(
        q.do(
            # delete product
            q.delete(
                q.ref(
                    q.collection('Product'),
                    data.split(';')[1]
                )
            ),
            # if product deleted is the last latest
            q.let(
                {
                    'biz_stack': q.if_(
                        q.is_empty(
                            q.match(
                                q.index("business-stack_by_name"),
                                context.user_data['sme_name']
                            )
                        ),
                        q.create(
                            q.collection('Business_Stack'),
                            {
                                'data': {
                                    'name': context.user_data['sme_name'],
                                    'stack': []
                                }
                            }
                        ),
                        q.get(
                            q.match(
                                q.index("business-stack_by_name"),
                                context.user_data['sme_name']
                            )
                        )
                    )
                },
                q.if_(
                    q.equals(data.split(';')[1], context.user_data['sme_latest']),
                    q.update(
                        q.select(
                            ['ref'],
                            q.var('biz_stack')
                        ),
                        {
                            "data": {
                                "stack": q.reverse(
                                    q.drop(1,
                                        q.reverse(
                                            q.select(
                                                ['data', 'stack'],
                                                q.var('biz_stack')
                                            )
                                        )
                                    )
                                )
                            }
                        }
                    ),
                    q.var('biz_stack')
                )
            )
        )
    )
    # update the sme's latest product
    update_sme_latest(context.user_data['sme_name'])

    button = [
        [
            InlineKeyboardButton(
                text="Go back to catalogue",
                callback_data=context.user_data['sme_name']
            )
        ]
    ]
    bot.send_message(
        chat_id=chat_id,
        text="Removed product from catalogue successfully! 🗑️",
        reply_markup=InlineKeyboardMarkup(button)
    )
    return SME_CATALOGUE


def update_product_info(update, context):
    bot = context.bot
    chat_id = update.message.chat.id
    data = parse_product_info(update.message.text)
    button = [
        [
            InlineKeyboardButton(
                text="Go back to catalogue",
                callback_data=context.user_data['sme_name']
            )
        ]
    ]
    if data is False:
        bot.send_message(
            chat_id=chat_id,
            text="Invalid Entry, please try again",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return SME_CATALOGUE
    # if it parsed the data correctly then we can update the product info
    try:
        client.query(
            q.update(
                q.ref(
                    q.collection('Product'),
                    context.user_data['product_id']
                ),
                {'data': data}
            )
        )
        bot.send_message(
            chat_id=chat_id,
            text="Updated product details succesfully!",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return SME_CATALOGUE
    except FaunaError as e:
        bot.send_message(
            chat_id=chat_id,
            text="An error occurred while trying to update the product, "
            "please try again!.",
            reply_markup=InlineKeyboardMarkup(button)
        )
        print(e)
        return SME_CATALOGUE


def show_catalogue(update, context):
    bot = context.bot
    chat_id = context.user_data['sme_chat_id']
    # fetch products owned by business
    products = client.query(
        q.map_(
            lambda x: q.get(x),
            q.paginate(
                q.match(
                    q.index("product_by_business"),
                    context.user_data['sme_name']
                )
            )
        )
    )
    if len(products['data']) == 0:
        button = [
            [
                InlineKeyboardButton(
                    text="Add products to your catalogue",
                    callback_data=chat_id
                )
            ]
        ]
        bot.send_message(
            chat_id=chat_id,
            text="Hi! 😃 you don't seem to have added any products yet!.",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return ADD_PRODUCTS
    for product in products["data"]:
        context.user_data["sme_name"] = product['data']['sme']
        button = [
            [
                InlineKeyboardButton(
                    text="Edit Info",
                    callback_data="Edit;" + product["ref"].id()
                )
            ],
            [
                InlineKeyboardButton(
                    text="Delete product from catalogue",
                    callback_data="Delete;" + product["ref"].id()
                )
            ]
        ]
        bot.send_photo(
            chat_id=chat_id,
            photo=product["data"]["image"],
            caption=f"{product['data']['name']} \nDescription: {product['data']['description']}\nPrice:{product['data']['price']}",
            reply_markup=InlineKeyboardMarkup(button)
        )
    return POST_VIEW_CATALOGUE
