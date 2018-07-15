from channels import route
from chat import consumers

channel_routing = [
    route("websocket.connect", consumers.ws_connect),
    route("websocket.receive", consumers.ws_receive),
    route("websocket.disconnect", consumers.ws_disconnect),

    route("treatment.receive", consumers.treatment_wait, command="^wait$"),
    route("treatment.receive", consumers.treatment_view, command="^view$"),
    route("treatment.receive", consumers.treatment_wake, command="^wake$"),
    route("treatment.receive", consumers.treatment_begin, command="^begin$"),
    route("treatment.receive", consumers.treatment_end, command="^end$"),
    route("treatment.receive", consumers.treatment_follow, command="^follow$"),
    route("treatment.receive", consumers.treatment_unfollow, command="^unfollow$"),
    route("treatment.receive", consumers.treatment_send, command="^send$"),
]
