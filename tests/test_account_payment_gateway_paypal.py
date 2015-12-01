# This file is part of the account_payment_gateway_paypal module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase


class AccountPaymentGatewayPaypalTestCase(ModuleTestCase):
    'Test Account Payment Gateway Paypal module'
    module = 'account_payment_gateway_paypal'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AccountPaymentGatewayPaypalTestCase))
    return suite