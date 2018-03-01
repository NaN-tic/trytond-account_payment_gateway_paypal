# This file is part account_payment_gateway_paypal module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import gateway


def register():
    Pool.register(
        gateway.AccountPaymentGateway,
        module='account_payment_gateway_paypal', type_='model')
