# This file is part account_payment_gateway_paypal module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval, Equal

__all__ = ['AccountPaymentGateway']


class AccountPaymentGateway:
    __metaclass__ = PoolMeta
    __name__ = 'account.payment.gateway'
    paypal_email = fields.Char('Email',
        states={
            'required': Equal(Eval('method'), 'paypal'),
            'invisible': ~(Equal(Eval('method'), 'paypal')),
        }, help='Paypal Email Account')

    @classmethod
    def get_methods(cls):
        res = super(AccountPaymentGateway, cls).get_methods()
        res.append(('paypal', 'Paypal'))
        return res
