from telegram.ext import (
    CommandHandler,
    ConversationHandler, MessageHandler,
    Filters, Updater, CallbackQueryHandler
)
from sme_handlers import (
    business_details, business_details_update,
    add_product, product_info,
    post_show_catalogue, update_product_info,
    show_catalogue
)
from customer_handlers import (
    customer_pref, show_products,
    post_view_products
)
from generic_handlers import (
    start, choose, classer,
    searcher, search_, cancel
)
from consts import (
    CHOOSING, CLASS_STATE, SME_DETAILS, SME_CAT, ADD_PRODUCTS,
    SHOW_STOCKS, POST_VIEW_PRODUCTS, SME_CATALOGUE,
    BIZ_SEARCH, POST_VIEW_CATALOGUE, CHOOSE_PREF
)
from config import TOKEN

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher


def main():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(
                    Filters.all, choose
                )
            ],
            CLASS_STATE: [
                CallbackQueryHandler(classer)
            ],
            SME_DETAILS: [
                MessageHandler(
                    Filters.all, business_details
                )
            ],
            SME_CAT: [
                CallbackQueryHandler(business_details_update)
            ],
            ADD_PRODUCTS: [
                CallbackQueryHandler(add_product),
                MessageHandler(Filters.all, product_info)
            ],
            CHOOSE_PREF: [
                CallbackQueryHandler(customer_pref)
            ],
            SHOW_STOCKS: [
                CallbackQueryHandler(show_products)
            ],
            POST_VIEW_PRODUCTS: [
                CallbackQueryHandler(post_view_products)
            ],
            BIZ_SEARCH: [
                MessageHandler(
                    Filters.all, searcher
                )
            ],
            SME_CATALOGUE: [
                CallbackQueryHandler(show_catalogue)
            ],
            POST_VIEW_CATALOGUE: [
                CallbackQueryHandler(post_show_catalogue),
                MessageHandler(Filters.all, update_product_info)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    dispatcher.add_handler(conv_handler)
    # extras
    search = CommandHandler('search', search_)
    dispatcher.add_handler(search)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
