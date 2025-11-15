import asyncio


class QueueManager:
    """
    Shared queue manager to manage and centralize the communication
    between modules
    """

    def __init__(self):
        self.to_bot: asyncio.Queue = asyncio.Queue()
        self.to_ws: asyncio.Queue = asyncio.Queue()


queue_manager = QueueManager()
