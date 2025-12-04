# debug_jwt.py — Enhanced JWT Diagnostic Tool
import json
import jwt
import time
from auth import generate_tableau_jwt, load_secrets

print("🔍 Loading secrets.json ...")
secrets = load_secrets()
print(json.dumps(secrets, indent=2))

print("\n🔑 Generating Tableau JWT...")
token = generate_tableau_jwt()

print("\n🟦 JWT (first 120 characters):")
print(token[:120] + " ...")

print("\n🧩 Decoding JWT (signature not verified)...")
payload = jwt.decode(token, options={"verify_signature": False})
print(json.dumps(payload, indent=2))

# ------------------------------------
# VALIDATION CHECKS
# ------------------------------------
now = int(time.time())
exp = payload.get("exp", 0)
ttl = exp - now

print("\n============================")
print("🔎 JWT VALIDATION CHECKS")
print("============================")

# Expiry checks
if ttl > 0:
    print(f"✅ Token is VALID for {ttl} more seconds ({ttl/60:.1f} minutes)")
else:
    print("❌ Token is EXPIRED!")
    print("⚠️ Please refresh token or increase TTL in generate_tableau_jwt().")

# Site GUID check
site_id = payload.get("site", {}).get("id")
if site_id == secrets.get("site_id"):
    print(f"✅ Site ID OK → {site_id}")
else:
    print("❌ Site ID mismatch!")
    print(f"Token site.id = {site_id}")
    print(f"Secrets site_id = {secrets.get('site_id')}")

# Scope check
scp = payload.get("scp", [])
if "tableau:views:embed" in scp:
    print("✅ Scope OK (tableau:views:embed enabled)")
else:
    print("❌ INVALID SCOPE → Must include tableau:views:embed")

# Subject check
sub = payload.get("sub")
print(f"👤 User impersonated (sub) → {sub}")

print("\n====================================")
print("🎉 FINAL RESULT")
print("====================================")
if ttl > 0 and site_id == secrets.get("site_id") and "tableau:views:embed" in scp:
    print("🎯 JWT is PERFECT — proceed to Streamlit.")
else:
    print("⚠️ Fix issues above before embedding in Streamlit.")

print("====================================")
