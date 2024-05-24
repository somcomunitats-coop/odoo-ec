from ..backends.base import Backend


class MonitoringService:
    def __init__(self, backend: Backend):
        self.backend = backend
