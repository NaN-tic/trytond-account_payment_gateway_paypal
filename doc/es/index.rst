==========================
Pasarelas de pagos. Paypal
==========================

Permite activar la pasarela de pago Paypal.

Paypal Classic
--------------

Se requeire paypal-python https://pypi.python.org/pypi/paypal/

Los datos de indentificación son "username", "passwod" y "signature".

El método TransactionSearch sólo devuelve llamadas con 100 registros.
No permite llamadas con más de 100 registros en cada intérvalo de fecha.

Paypal REST SDK
---------------

Se requeire paypalrestsdk https://pypi.python.org/pypi/paypalrestsdk

Los datos de indentificación son "client_id" i "client_secret" de Paypal App.
