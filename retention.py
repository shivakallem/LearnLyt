def get_revision_days(score, previous_score=None):
    if score < 70:
        return 1
    if score < 85:
        return 2
    if score < 95:
        return 3
    return 5 if previous_score is not None and previous_score >= 85 else 3


def get_retention_status(score):
    if score < 50:
        return "Needs Improvement"
    if score < 70:
        return "Weak"
    if score < 85:
        return "Moderate"
    if score < 95:
        return "Good"
    return "Excellent"