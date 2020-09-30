# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 07:24:00 2020

@author: z003vrzk
"""

"""The Application class no longer requires a value for the localDevice or
localAddress parameters. BACpypes applications like that omit these parameters
will only be able to initiate confirmed or unconfirmed services that do not
require these objects or values.

They would not be able to respond to Who-Is requests for example.

Client-only applications are useful when it would be advantageous to avoid the
administrative overhead for configuring
something as a device, such as network analysis applications and very simple
trend data gather applications. They are
also useful for BACpypes applications that run in a Docker container or
“in the cloud”.
Sample client-only applications will be forthcoming."""