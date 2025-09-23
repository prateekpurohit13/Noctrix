PERMS = {
    "upload:create": {"Analyst","Admin"},
    "asset:read":    {"Analyst","Reviewer","Admin"},
    "export:create": {"Analyst","Admin"},
    "key:rotate":    {"Admin"},
}

def allowed(role: str, action: str) -> bool:
    return role in PERMS.get(action, set())
