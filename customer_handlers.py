from extensions import client
from faunadb import query as q
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup
)
from faunadb.errors import NotFound
from consts import (
    SHOW_STOCKS, CLASS_STATE, POST_VIEW_PRODUCTS
)
import os


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
                        callback_data="pref" + ',' + sme["data"]["name"]
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
    if "pref" in data:
        data = data.split(',')[1]
        print(data)
        user = client.query(
            q.get(
                q.match(
                    q.index('user_by_name'),
                    context.user_data['user-data']['name']
                )
            )
        )
        # update preference
        client.query(
            q.update(
                q.ref(
                    q.collection('User'), user['ref'].id()
                ),
                {'data': {'preference': user['data']['preference'] + data + ','}}
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
            ],
            [
                InlineKeyboardButton(
                    text="Add Item To Cart",
                    callback_data="cart;" + product["ref"].id()
                )
            ]
        ]
        context.user_data['product_price'] = product['data']['price']
        context.user_data['product_id'] = product['ref'].id()
        context.user_data['product_name'] = product['data']['name']
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
    elif 'cart' in data:
        # add product details to cart
        client.query(
            q.do(
                q.let(
                    {
                        "cart": q.if_(
                            q.is_empty(
                                q.match(
                                    q.index('cart_by_chat_id'),
                                    chat_id
                                )
                            ),
                            q.pow(2, 3),
                            q.get(
                                q.match(
                                    q.index('cart_by_chat_id'),
                                    chat_id
                                )
                            )
                        )
                    },

                    q.update(
                        q.select(['ref'], q.var('cart')),
                        {
                            "data": {
                                "items": q.append(
                                    {
                                        'product_id': context.user_data['product_id'],
                                        'product': context.user_data['product_name'],
                                        'price': context.user_data['product_price']
                                    },
                                    q.select(['data', 'items'], q.var('cart'))
                                )
                            }
                        }
                    )
                )
            )
        )
        # send response
        bot.send_message(
            chat_id=chat_id,
            text="Item Added to cart"
        )


def cart(update, context):
    bot = context.bot
    chat_id = update.message.chat.id
    # get user cart
    cart = client.query(
        q.get(
            q.match(
                q.index('cart_by_chat_id'),
                chat_id
            )
        )
    )
    bot.send_message(
        chat_id=chat_id,
        text=f"Here's your unique cart id {cart['ref'].id()}"
    )
    bot.send_message(
        chat_id=chat_id,
        text=f"Click on this link to go to the checkout page -> {os.getenv('CHECKOUT_PAGE')}"
    )
    return CLASS_STATE
