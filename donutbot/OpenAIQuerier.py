from openai import OpenAI
client = OpenAI()

class OpenAIQuerier:

    def analyse_pic(self, url: str) -> int:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "If there are donuts on this picture, return the number of donut(s). If not return 0. Only return a single integer with no additional text."},
                    {
                        "type": "input_image",
                        "image_url": url,
                    },
                ],
            }], # type: ignore
        )

        try:
            return int(response.output_text)
        except ValueError:
            print(f"Unexpected LLM output: {response.output_text}")
            return 0
