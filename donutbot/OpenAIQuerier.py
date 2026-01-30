from openai import OpenAI

from Config import config

client = OpenAI(api_key=config.settings["openAI"]["api_key"])

class OpenAIQuerier:

    def analyse_pic(self, url: str) -> int:
        response = client.responses.create(
            model=config.settings["openAI"]["model"],
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text",
                     "text": config.settings["openAI"]["prompt"]},
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
