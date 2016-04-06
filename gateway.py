# This file is part account_payment_gateway_paypal module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import paypalrestsdk
import iso8601
import logging
from datetime import datetime
from decimal import Decimal
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval, Equal


__all__ = ['AccountPaymentGateway']

logger = logging.getLogger(__name__)

_PAYPAL_STATE = {
    'created': 'draft',
    'approved': 'authorized',
    'failed': 'cancel',
    'pending': 'draft',
    'canceled': 'cancel',
    'expired': 'cancel',
    'in_progress': 'authorized',
    }

class AccountPaymentGateway:
    __metaclass__ = PoolMeta
    __name__ = 'account.payment.gateway'
    paypal_email = fields.Char('Email',
        states={
            'required': Equal(Eval('method'), 'paypal'),
            'invisible': ~(Equal(Eval('method'), 'paypal')),
        }, help='Paypal Email Account')
    paypal_client_id = fields.Char('Client ID',
        states={
            'invisible': ~(Equal(Eval('method'), 'paypal')),
        }, help='Paypal Rest APP Client ID')
    paypal_client_secret = fields.Char('Client Secret',
        states={
            'invisible': ~(Equal(Eval('method'), 'paypal')),
        }, help='Paypal Rest APP Client Secret')

    @classmethod
    def __setup__(cls):
        super(AccountPaymentGateway, cls).__setup__()
        cls._error_messages.update({
            'paypal_client': 'Register for a Paypal developer account and get your '
                'client_id and secret',
        })

    @classmethod
    def get_methods(cls):
        res = super(AccountPaymentGateway, cls).get_methods()
        res.append(('paypal', 'Paypal'))
        return res

    def _get_gateway_paypal(self, data):
        '''
        Return gateway for an transaction
        '''
        Currency = Pool().get('currency.currency')

        uuid = data['id']
        ct = iso8601.parse_date(data['create_time'])
        trans_date = datetime(ct.year, ct.month, ct.day)
        state = data['state']
        pay_trans = data['transactions'][0]
        description = pay_trans['description']
        amount = Decimal(pay_trans['amount']['total'])
        currency_code = pay_trans['amount']['currency']
        currency, = Currency.search([
            ('code', '=', currency_code),
            ])

        return {
            'uuid': uuid,
            'description': description,
            #~ 'origin': v[''],
            'gateway': self,
            'reference_gateway': description,
            'authorisation_code': uuid, # TODO ?
            'date': trans_date,
            #~ 'company': v[''],
            #~ 'party': v[''],
            'amount': amount,
            'currency': currency,
            'state': _PAYPAL_STATE[state],
            'log': str(data),
            }

    def import_transactions_paypal(self, ofilter=None):
        '''
        Import Paypal Transactions
        :param ofilter: dict
        '''
        GatewayTransaction = Pool().get('account.payment.gateway.transaction')

        now = datetime.now()

        if not self.paypal_client_id and not self.paypal_client_secret:
            self.raise_user_error('paypal_client')

        paypalrestsdk.configure({
            "mode": self.mode, # sandbox or live
            "client_id": self.paypal_client_id,
            "client_secret": self.paypal_client_secret,
            })

        # Update date last import
        start_time = self.from_transactions
        end_time = self.to_transactions
        self.write([self], {'from_transactions': now, 'to_transactions': None})
        Transaction().cursor.commit()

        # https://developer.paypal.com/docs/api/#list-payment-resources
        ofilter = {}
        ofilter['start_time'] = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        if end_time:
            ofilter['end_time'] = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        paypal_payments = paypalrestsdk.Payment.all(ofilter)

        if not getattr(paypal_payments, 'payments'):
            return

        payments = {}
        for payment in paypal_payments.payments:
            payments[payment['id']] = payment

        paypal_uuids = [k for k, _ in payments.iteritems()]
        uuids = [t.uuid for t in GatewayTransaction.search([
            ('uuid', 'in', paypal_uuids),
            ])]

        to_create = []
        for uuid, v in payments.iteritems():
            if k in uuids:
                continue
            to_create.append(self._get_gateway_paypal(v))

        if to_create:
            GatewayTransaction.create(to_create)
            logger.info('Imported %s Paypal transactions.' % (len(to_create)))
