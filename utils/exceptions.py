class VFATDACBiasCannotBeReached(ValueError):
    def __init__(self, message, errors):
        super(VFATDACBiasCannotBeReached, self).__init__(message)

        self.errors = errors
        return
