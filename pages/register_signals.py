from django.dispatch import Signal

room_joined = Signal()
kicked_from_room = Signal()
kicked_from_session = Signal()
left_session = Signal()
left_room = Signal()
owner_transferred = Signal()
session_created = Signal()
task_completed = Signal()
task_created = Signal()


session_joined = Signal()

session_started = Signal()
session_ended = Signal()
