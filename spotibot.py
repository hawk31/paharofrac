import os
import logging
import pandas as pd
import time
from telegram.ext import Updater, CommandHandler

logging.basicConfig(format='%(acstime)s - %(name) - %(levelname)s - %(message)s',
                    level=logging.INFO)


users = ['hawk31', 'pho', 'Nekmo', 'Guixu', 'Manuel', 'Bea']

class SpotiBot:
    def __init__(self, token):
        """
        Initializes bot with given token.
        """
        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher
        self.df = pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'payment.csv'))

        self.presentation_handler = CommandHandler('presentation', self.presentation)
        self.payment_handler = CommandHandler('paymentstatus', self.paymentstatus, pass_args=True)
        self.update_handler = CommandHandler('update', self.update_handler, pass_args=True)

        self.dispatcher.add_handler(self.presentation_handler)
        self.dispatcher.add_handler(self.payment_handler)
        self.dispatcher.add_handler(self.update_handler)
        self.updater.start_polling()

    def presentation(self, bot, update):
        """
        Presents the bot to the world.
        """
        bot.send_message(chat_id=update.message.chat_id, text='Holi, me dedico a cobrar la coca de vez en cuando. PANDA DE MOROSOS')

    def paymentstatus(self, bot, update, args):
        if len(args) != 1 and isinstance(args, list):
            bot.send_message(chat_id=update.message.chat_id, text='This method only accepts a single argument')
            return
        user = args[0]
        if user not in users:
            bot.send_message(chat_id=update.message.chat_id, text='User does not belong in group.')
            return
        user_data = self.df[self.df.User == user]
        msg = 'User {} last paid in {}, and has payment due in {}'.format(user_data['User'].as_matrix()[0], user_data['Last Paid'].as_matrix()[0], user_data['Paid until'].as_matrix()[0])
        bot.send_message(chat_id=update.message.chat_id, text=msg)

    def update_handler(self, bot, update, args):
        if len(args) != 2 and isinstance(args, list):
            bot.send_message(chat_id=update.message.chat_id, text='This method only accepts two arguments, user and date.')
            return
        user = args[0]
        date = args[1]

        if len(args[1]) != 10:
            bot.send_message(chat_id=update.message.chat_id, text='Me pones la fecha como dios manda, por favor. `dd/mm/yyyy`')
            return
        if user not in users:
            bot.send_message(chat_id=update.message.chat_id, text='User does not belong in group.')
            return

        self.df.loc[self.df.User == user, 'Last Paid'] = str(time.strftime("%d/%m/%Y"))
        self.df.loc[self.df.User == user, 'Paid until']  = date

        bot.send_message(chat_id=update.message.chat_id, text='Updated correctly. @hawk31 has been notified.')
        self.df.to_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'payment.csv'), index=False)
        self.df = pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'payment.csv'))

