"""Fixed V1.23 genesis authority; candidate DDL awaits Task 4A."""
from joy_m2.errors import InputFormatError
from .v122_writer_profiles import canonical_json_file_bytes, sha256_bytes

BASELINE_SHA256 = "a474846a5b1d10a0fe48a259522fbb327747319f4a114452bf9f294405d8d9e0"
BASELINE_SIZE_BYTES = 10_510_336
BASELINE_MANIFEST_SHA256 = "441e00ac1536b959b40b6177bd17a6f14632a287f85145e202a51bcf137ddc8b"
BASELINE_MANIFEST_SIZE_BYTES = 7_915
BASELINE_RELEASE_DIGEST = "89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b"
GENESIS_DIGEST = "ea3b7db78210e045761784a2e415387c1b17f13b5aedde484ca2ae248a45eec7"

def _genesis_digest() -> str:
    """Reconstruct the fixed first-parent authority, never from artifacts."""
    projection = {
        "baseline_database_sha256": BASELINE_SHA256,
        "baseline_question_count": 639,
        "baseline_release_digest": BASELINE_RELEASE_DIGEST,
        "baseline_release_version": "V1.22", "candidate_count": 0,
        "schema": "task13-v123-genesis-v1", "target_release_version": "V1.23",
    }
    actual = sha256_bytes(canonical_json_file_bytes(projection))
    if actual != "ea3b7db78210e045761784a2e415387c1b17f13b5aedde484ca2ae248a45eec7":
        raise InputFormatError("V1.23 genesis projection mismatch")
    return actual
