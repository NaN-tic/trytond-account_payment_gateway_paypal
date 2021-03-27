# This file is part account_payment_gateway_paypal module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import iso8601
import logging
from datetime import datetime
from decimal import Decimal
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval, Equal
from trytond.modules.account_payment_gateway.tools import unaccent

PAYPAL_METHODS = []
try:
    import paypalrestsdk
    PAYPAL_METHODS.append(('restsdk', 'REST SDK'))
except ImportError:
    pass
try:
    from paypal import PayPalInterface
    PAYPAL_METHODS.append(('soap', 'SOAP (Classic)'))
except ImportError:
    pass

logger = logging.getLogger(__name__)

_PAYPAL_STATE = {
    'created': 'draft',
    'approved': 'authorized',
    'failed': 'cancelled',
    'pending': 'draft',
    'canceled': 'cancelled',
    'expired': 'cancelled',
    'in_progress': 'authorized',
    'Pending': 'draft',
    'Processing': 'authorized',
    'Success': 'authorized',
    'Denied': 'cancelled',
    'Reversed': 'cancelled',
    'Completed': 'authorized',
    }
_PAYPAL_KEYS = (
    'L_TRANSACTIONID',
    'L_STATUS',
    'L_NAME',
    'L_TIMEZONE',
    'L_TIMESTAMP',
    'L_CURRENCYCODE',
    'L_TYPE',
    'L_EMAIL',
    'L_AMT',
    'L_NETAMT',
    )


class AccountPaymentGateway(metaclass=PoolMeta):
    __name__ = 'account.payment.gateway'

    # Two methods: REST SDK (Paypal App) + SOAP (Classic)
    paypal_method = fields.Selection(PAYPAL_METHODS, 'Paypal Methods',
        help='Select a API Paypal method to connect.')
    paypal_email = fields.Char('Email',
        states={
            'required': Equal(Eval('method'), 'paypal'),
            'invisible': ~(Equal(Eval('method'), 'paypal')),
        }, help='Paypal Email Account')
    paypal_username = fields.Char('Username',
        states={
            'invisible': (~(Equal(Eval('method'), 'paypal'))
                | ~(Equal(Eval('paypal_method'), 'soap'))),
            'required': ((Equal(Eval('method'), 'paypal'))
                & (Equal(Eval('paypal_method'), 'soap'))),
        }, help='Paypal Username Soap API')
    paypal_password = fields.Char('Password',
        states={
            'invisible': (~(Equal(Eval('method'), 'paypal'))
                | ~(Equal(Eval('paypal_method'), 'soap'))),
            'required': ((Equal(Eval('method'), 'paypal'))
                & (Equal(Eval('paypal_method'), 'soap'))),
        }, help='Paypal Password Soap API')
    paypal_signature = fields.Char('Signature',
        states={
            'invisible': (~(Equal(Eval('method'), 'paypal'))
                | ~(Equal(Eval('paypal_method'), 'soap'))),
            'required': ((Equal(Eval('method'), 'paypal'))
                & (Equal(Eval('paypal_method'), 'soap'))),
        }, help='Paypal Signature Soap API')
    paypal_client_id = fields.Char('Client ID',
        states={
            'invisible': (~(Equal(Eval('method'), 'paypal'))
                | ~(Equal(Eval('paypal_method'), 'restsdk'))),
            'required': ((Equal(Eval('method'), 'paypal'))
                & (Equal(Eval('paypal_method'), 'restsdk'))),
        }, help='Paypal Rest APP Client ID')
    paypal_client_secret = fields.Char('Client Secret',
        states={
            'invisible': (~(Equal(Eval('method'), 'paypal'))
                | ~(Equal(Eval('paypal_method'), 'restsdk'))),
            'required': ((Equal(Eval('method'), 'paypal'))
                & (Equal(Eval('paypal_method'), 'restsdk'))),
        }, help='Paypal Rest APP Client Secret')


    @classmethod
    def get_methods(cls):
        res = super(AccountPaymentGateway, cls).get_methods()
        res.append(('paypal', 'Paypal'))
        return res

    def _get_gateway_paypal_restsdk(self, data):
        '''
        Return gateway for an transaction
        '''
        Currency = Pool().get('currency.currency')

        uuid = data['id']
        ct = iso8601.parse_date(data['create_time'])
        trans_date = datetime(ct.year, ct.month, ct.day)
        state = _PAYPAL_STATE[data['state']]
        pay_trans = data['transactions'][0]
        try:
            description = unaccent(pay_trans['description'])
        except KeyError:
            description = ''
        amount = Decimal(pay_trans['amount']['total'])
        currency_code = pay_trans['amount']['currency']
        currency, = Currency.search([
            ('code', '=', currency_code),
            ])

        return {
            'uuid': uuid,
            'description': description,
            #  'origin': v[''],
            'gateway': self,
            'reference_gateway': description,
            'authorisation_code': uuid,  # TODO ?
            'date': trans_date,
            #  'company': v[''],
            #  'party': v[''],
            'amount': amount,
            'currency': currency,
            'state': state,
            'log': str(data),
            }

    def _get_gateway_paypal_soap(self, data):
        '''
        Return gateway for an transaction
        '''
        pool = Pool()
        Currency = pool.get('currency.currency')
        Party = pool.get('party.party')

        uuid = data['L_TRANSACTIONID']
        ct = iso8601.parse_date(data['L_TIMESTAMP'])
        trans_date = datetime(ct.year, ct.month, ct.day)
        state = _PAYPAL_STATE[data['L_STATUS']]
        # not available description
        description = '%s - %s' % (unaccent(data['L_NAME']), data['L_EMAIL'])
        amount = Decimal(data['L_AMT'])
        currency_code = data['L_CURRENCYCODE']
        currency, = Currency.search([
            ('code', '=', currency_code),
            ])

        # search a party with email
        parties = Party.search([
            ('rec_name', '=', data['L_EMAIL']),
            ])
        if parties:
            party, = parties
        else:
            party = None

        return {
            'uuid': uuid,
            'description': description,
            #  'origin': v[''],
            'gateway': self,
            'reference_gateway': description,
            'authorisation_code': uuid,  # TODO ?
            'date': trans_date,
            #  'company': v[''],
            'party': party,
            'amount': amount,
            'currency': currency,
            'state': state,
            'log': str(data),
            }

    def import_transactions_paypal_restsdk(self, start_time, end_time):
        '''Paypal REST SDK'''
        GatewayTransaction = Pool().get('account.payment.gateway.transaction')

        # https://developer.paypal.com/docs/api/#list-payment-resources
        ofilter = {}
        ofilter['start_time'] = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        if end_time:
            ofilter['end_time'] = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        paypalrestsdk.configure({
            "mode": self.mode,  # sandbox or live
            "client_id": self.paypal_client_id,
            "client_secret": self.paypal_client_secret,
            })

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
            if uuid in uuids:
                continue
            to_create.append(self._get_gateway_paypal_restsdk(v))
        return to_create

    def import_transactions_paypal_soap(self, start_time, end_time):
        '''Paypal SOAP'''
        GatewayTransaction = Pool().get('account.payment.gateway.transaction')

        # https://developer.paypal.com/webapps/developer/docs/classic/products/
        # https://developer.paypal.com/docs/classic/api/merchant/TransactionSearch_API_Operation_SOAP/
        ofilter = {}
        ofilter['STARTDATE'] = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        if end_time:
            ofilter['ENDDATE'] = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        paypal_api = PayPalInterface(
            API_USERNAME=self.paypal_username,
            API_PASSWORD=self.paypal_password,
            API_SIGNATURE=self.paypal_signature,
            API_ENVIRONMENT='PRODUCTION' if self.mode == 'live' else 'SANDBOX',
            DEBUG_LEVEL=0,
            HTTP_TIMEOUT=30,
            )
        transactions = paypal_api.transaction_search(**ofilter)

        # convert raw values to dict with ID key to process later payment data
        payments = {}
        for k, v in transactions.raw.iteritems():
            if k.startswith(_PAYPAL_KEYS):
                for l in _PAYPAL_KEYS:
                    if k.startswith(l):
                        break
                id_ = k.replace(l, '')

                if id_ not in payments:
                    payments[id_] = {l: v[0]}
                else:
                    payments[id_][l] = v[0]

        paypal_uuids = [v['L_TRANSACTIONID'] for _, v in payments.iteritems()]
        uuids = [t.uuid for t in GatewayTransaction.search([
            ('uuid', 'in', paypal_uuids),
            ])]

        to_create = []
        for k, v in payments.iteritems():
            # filter payment type (L_TYPE). For example filter 'Transfer' type
            if v['L_TYPE'] not in ['Payment']:
                continue
            if v['L_TRANSACTIONID'] in uuids:
                continue
            to_create.append(self._get_gateway_paypal_soap(v))

        return to_create

    def import_transactions_paypal(self):
        '''Import Paypal Transactions - REST SDK or Soap (Classic)'''
        GatewayTransaction = Pool().get('account.payment.gateway.transaction')

        now = datetime.now()

        # Update date last import
        start_time = self.from_transactions
        end_time = self.to_transactions
        self.write([self], {'from_transactions': now, 'to_transactions': None})
        Transaction().cursor.commit()

        import_paypal = getattr(self, 'import_transactions_paypal_%s' %
            self.paypal_method)
        to_create = import_paypal(start_time, end_time)

        if to_create:
            GatewayTransaction.create(to_create)
            logger.info('Imported %s Paypal transactions.' % (len(to_create)))
