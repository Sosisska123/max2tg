import asyncio


class QueueManager:
    """
    Shared queue manager to manage and centralize the communication
    between modules
    """

    def __init__(self):
        self.to_bot: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.to_ws: asyncio.Queue = asyncio.Queue(maxsize=1000)


_queue_manager = None


def get_queue_manager() -> QueueManager:
    global _queue_manager

    if _queue_manager is None:
        _queue_manager = QueueManager()

    return _queue_manager
