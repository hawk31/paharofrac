import logging
import os
from datetime import datetime, time

import pandas as pd
from telegram.ext import CommandHandler, Updater

logging.basicConfig(format='%(acstime)s - %(name) - %(levelname)s - %(message)s',
                    level=logging.INFO)


users = ['@hawk31', '@phofe', '@nekmo', '@unaperalimonera', '@bearc11']
datef = '%d/%m/%Y'


class SpotiBot:
    def __init__(self, token):
        """
        Initializes bot with given token.
        """
        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher
        self.queue = self.updater.job_queue
        self.df = pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'payment.csv'))

        self.presentation_handler = CommandHandler('presentation', self.presentation)
        self.payment_handler = CommandHandler('paymentstatus', self.payment_status, pass_args=True)
        self.update_handler = CommandHandler('update', self.update, pass_args=True)
        self.overall_handler = CommandHandler('overallstatus', self.overall_status)
        self.timer_handler = CommandHandler('timer', self.callback_timer, pass_job_queue=True)

        self.dispatcher.add_handler(self.presentation_handler)
        self.dispatcher.add_handler(self.payment_handler)
        self.dispatcher.add_handler(self.update_handler)
        self.dispatcher.add_handler(self.overall_handler)
        self.dispatcher.add_handler(self.timer_handler)

        self.updater.start_polling()

    def presentation(self, bot, update):
        """
        Presents the bot to the world.
        """
        bot.send_message(chat_id=update.message.chat_id, text='Paguen la coca.')

    def payment_status(self, bot, update, args):
        if len(args) != 1 and isinstance(args, list):
            bot.send_message(chat_id=update.message.chat_id, text='Usage: `/paymentstatus user`')
            return
        user = args[0]
        if user not in users:
            bot.send_message(chat_id=update.message.chat_id, text='User does not belong in group.')
            return
        user_data = self.df[self.df.User == user]
        msg = 'User {} last paid in {}, and has payment due in {}'.format(user_data['User'].as_matrix()[0], user_data['Last Paid'].as_matrix()[0], user_data['Paid until'].as_matrix()[0])
        bot.send_message(chat_id=update.message.chat_id, text=msg)

    def update(self, bot, update, args):
        if len(args) != 2 and isinstance(args, list):
            bot.send_message(chat_id=update.message.chat_id, text='This method only accepts two arguments, user and date.')
            return
        user = args[0]
        try:
            date = datetime.strptime(args[1], datef)
        except ValueError:
            bot.send_message(chat_id=update.message.chat_id, text='Me pones la fecha como dios manda, por favor. `dd/mm/yyyy`')
            return
        if user not in users:
            bot.send_message(chat_id=update.message.chat_id, text='User does not belong in group.')
            return

        self.df.loc[self.df.User == user, 'Last Paid'] =  datetime.now().strftime(datef)
        self.df.loc[self.df.User == user, 'Paid until']  = date.strftime(datef)

        bot.send_message(chat_id=update.message.chat_id, text='Updated correctly. @hawk31 has been notified.')
        self.df.to_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'payment.csv'), index=False)
        self.df = pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'payment.csv'))

    def compute_morosos(self):
        morosos = []
        less_month = []

        for index, item in self.df.iterrows():
            user = item['User']
            last_paid = datetime.strptime(item['Last Paid'], datef)
            paid_until = datetime.strptime(item['Paid until'], datef)
            delta = (paid_until - last_paid).days
            if delta < 0:
                morosos.append(user)
            if delta < 30 and user not in morosos:
                less_month.append(user)
        morosos = ''.join(m + ', ' for m in morosos).strip()[:-1]
        less_month = ''.join(m + ', ' for m in less_month).strip()[:-1]
        return morosos, less_month 

    def overall_status(self, bot, update):
        morosos, less_month = self.compute_morosos()
        if len(morosos) > 0:
            bot.send_message(chat_id=update.message.chat_id,
                             text='Estos son unos morosos que no pagan la coca: {}'.format(morosos))
        if len(less_month) > 0:
            bot.send_message(chat_id=update.message.chat_id,
                             text='Tienen que pagar en menos de un mes: {}'.format(less_month))

    def callback_morosos(self, bot, job):
        morosos, less_month = self.compute_morosos()
        if len(morosos) > 0:
            bot.send_message(chat_id=job.context,
                             text='Estos son unos morosos que no pagan la coca: {}'.format(morosos))
        if len(less_month) > 0:
            bot.send_message(chat_id=job.context,
                             text='Tienen que pagar en menos de un mes: {}'.format(less_month))

    def callback_timer(self, bot, update, job_queue):
        bot.send_message(chat_id=update.message.chat_id, text='Cada semana os avisaré de pagos, guapos.')
        self.queue.run_daily(self.callback_morosos, time=time(12, 00),
                             days=(6,), context=update.message.chat_id)
