"""Permission boundary demonstration; caller identity comes from trusted app context."""
from pydantic import BaseModel, ConfigDict, Field


class LookupArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    ticket_id: str = Field(min_length=1, max_length=20)


TICKETS = {"T1": {"owner": "demo-user", "status": "open"}, "T2": {"owner": "another-user", "status": "closed"}}


def dispatch(tool_name, arguments, *, authenticated_user):
    if tool_name != "lookup_ticket":
        raise PermissionError("Tool is not allowed")
    args = LookupArgs.model_validate(arguments)
    ticket = TICKETS.get(args.ticket_id)
    if ticket is None or ticket["owner"] != authenticated_user:
        raise PermissionError("Ticket not accessible")
    return {"ticket_id": args.ticket_id, "status": ticket["status"]}
