class Proxy():
    """
    Pack some proxy info.
    """

    def __init__(self,
                 name='bypass',
                 ip_address='bypass',
                 port=0,
                 auth_user=None,
                 auth_pass=None):
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.auth_user = auth_user
        self.auth_pass = auth_pass
        if ip_address == 'bypass':
            self.is_bypass = True
        else:
            self.is_bypass = False
