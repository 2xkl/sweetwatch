"""AI agent for CGM trend analysis and predictions."""

import anthropic


class GlucoseAnalyzer:
    """Uses Claude API to analyze glucose trends and make predictions."""

    def __init__(self, api_key: str) -> None:
        self.client = anthropic.Anthropic(api_key=api_key)

    def analyze_trend(self, readings: list[dict]) -> str:
        """Analyze a series of glucose readings and return insights."""
        readings_text = "\n".join(
            f"  {r['timestamp']}: {r['value']} mg/dL" for r in readings
        )
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are a glucose trend analyst. Analyze the following CGM readings "
                        "and provide: 1) current trend direction, 2) rate of change, "
                        "3) prediction for next 30 minutes, 4) any alerts.\n\n"
                        f"Readings:\n{readings_text}"
                    ),
                }
            ],
        )
        return message.content[0].text
