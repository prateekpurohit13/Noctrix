import os, base64, sys

for k in ("KEK_BASE64", "NEW_KEK_BASE64"):
    s = os.environ.get(k)
    if not s:
        print(k, "is MISSING")
        sys.exit(1)
    try:
        base64.b64decode(s)
        print(k, "OK (len:", len(s), ")")
    except Exception as e:
        print(k, "BAD:", repr(s), e)
        sys.exit(1)

print("All good")
