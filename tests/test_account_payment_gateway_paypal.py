# This file is part of the account_payment_gateway_paypal module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest

try:
    import paypalrestsdk
except ImportError:
    paypalrestsdk = None

try:
    import paypal
except ImportError:
    paypal = None

import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool
from trytond.modules.currency.tests import create_currency
from datetime import datetime, timedelta


class AccountPaymentGatewayPaypalTestCase(ModuleTestCase):
    'Test Account Payment Gateway Paypal module'
    module = 'account_payment_gateway_paypal'

    @unittest.skipIf(not paypal, "missing paypal module")
    @with_transaction()
    def test_paypal_soap(self):
        'Import Paypal SOAP'
        pool = Pool()
        Gateway = pool.get('account.payment.gateway')

        # start_time = datetime.now() - timedelta(hours=1)
        # end_time = None

        gateway = Gateway()
        gateway.name = 'Paypal SOAP'
        gateway.method = 'paypal'
        gateway.mode = 'sandbox'
        gateway.paypal_method = 'soap'
        gateway.paypal_email = 'user@domain.com'
        gateway.paypal_username = 'xxxxxxxxxx'  # Unkwon test user
        gateway.paypal_password = 'xxxxxxxxxx'  # Unkwon test user
        gateway.paypal_signature = 'xxxxxxxxxx'  # Unkwon test user

        # test connection and process data
        # gateway.import_transactions_paypal_soap(start_time, end_time)
        # 'Security header is not valid' (Error Code: 10002)

    @unittest.skipIf(not paypalrestsdk, "missing paypalrestsdk module")
    @with_transaction()
    def test_paypal_restsdk(self):
        'Import Paypal REST SDK'
        pool = Pool()
        Gateway = pool.get('account.payment.gateway')

        create_currency('USD')

        start_time = datetime.now() - timedelta(hours=1)
        end_time = None

        gateway = Gateway()
        gateway.name = 'Paypal REST SDK'
        gateway.method = 'paypal'
        gateway.mode = 'sandbox'
        gateway.paypal_method = 'restsdk'
        gateway.paypal_client_id = (
            'EBWKjlELKMYqRNQ6sYvFo64FtaRLRR5BdHEESmha49TM')
        gateway.paypal_client_secret = (
            'EO422dn3gQLgDbuwqTjzrFgFtaRLRR5BdHEESmha49TM')

        # test connection and process data
        gateway.import_transactions_paypal_restsdk(start_time, end_time)


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AccountPaymentGatewayPaypalTestCase))
    return suite
