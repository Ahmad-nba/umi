FEEDBACK_ANALYSIS_PROMPT = """
You are classifying a feedback report for UMI.
Return valid JSON only with keys: summary, category, issue_type, priority, department, confidence.
Only use these enum values: priority in [LOW, MEDIUM, HIGH, CRITICAL], department in [Academic Affairs, IT, Facilities, Administration].
The summary must be concise and actionable.
"""
