def validate_role(role: str) -> str:
    allowed_roles = {"user", "assistant", "system"}
    role = role.strip().lower()
    if role not in allowed_roles:
        raise ValueError(
            f"Invalid role '{role}'. Must be one of: {allowed_roles}"
        )
    return role


def validate_score(score: float) -> float:
    if not isinstance(score, (int, float)):
        raise ValueError(f"Score must be numeric, got {type(score)}")
    if not (0.0 <= score <= 1.0):
        raise ValueError(f"Score must be between 0 and 1, got {score}")
    return float(score)
