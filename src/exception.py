class MissEnvException(Exception):
    def __init__(self, env):
        self.message = "Missing environment variable " + env 
