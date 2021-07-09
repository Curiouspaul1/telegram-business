import handlers
from telegram.ext import (
    CommandHandler, CallbackContext,
    ConversationHandler, MessageHandler,
    Filters, Updater, CallbackQueryHandler
)
from config import TOKEN

updater = Updater(token=TOKEN, use_context=True)
print(updater)
dispatcher = updater.dispatcher


def main():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', handlers.start)],
        states={
            handlers.CHOOSING: [
                MessageHandler(
                    Filters.all, handlers.choose
                )
            ],
            handlers.CLASS_STATE: [
                CallbackQueryHandler(handlers.classer)
            ],
            handlers.SME_DETAILS: [
                MessageHandler(
                    Filters.all, handlers.business_details
                )
            ],
            handlers.SME_CAT: [
                CallbackQueryHandler(handlers.business_details_update)
            ],
            handlers.ADD_PRODUCTS: [
                CallbackQueryHandler(handlers.add_product),
                MessageHandler(Filters.all, handlers.product_info)
            ],
            handlers.CHOOSE_PREF: [
                CallbackQueryHandler(handlers.customer_pref)
            ],
            handlers.SHOW_STOCKS: [
                CallbackQueryHandler(handlers.show_products)
            ],
            handlers.POST_VIEW_PRODUCTS: [
                CallbackQueryHandler(handlers.post_view_products)
            ],
            handlers.SEARCH: [
                MessageHandler(handlers.search)
            ]
        },
        fallbacks=[CommandHandler('cancel', handlers.cancel)],
        allow_reentry=True
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()