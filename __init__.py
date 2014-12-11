# This file is part account_payment_gateway_paypal module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from .gateway import *

def register():
    Pool.register(
        AccountPaymentGateway,
        module='account_payment_gateway_paypal', type_='model')
