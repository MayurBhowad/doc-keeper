from document_reader.llm.openai import OpenAIClient


class FakeResponse:

    def __init__(self):
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        class Response:
            output_text = """
                {
                    "invoice_number": "INV-123",
                    "vendor_name": "ABC Pvt Ltd",
                    "total": 15000
                }
                """
        return Response()


class FakeOpenAI:
    class responses:

        last_kwargs = None

        @staticmethod
        def create(**kwargs):
            FakeOpenAI.responses.last_kwargs = kwargs
            class Response:
                output_text = """
                    {
                        "invoice_number": "INV-123",
                        "vendor_name": "ABC Pvt Ltd",
                        "total": 15000
                    }
                """
            return Response()


def test_openai_client():
    fake_openai = FakeOpenAI()

    client = OpenAIClient.__new__(OpenAIClient)
    client.client = fake_openai
    client.model = "test-model"

    result = client.generate("Extract invoice number")

    assert result == """
                    {
                        "invoice_number": "INV-123",
                        "vendor_name": "ABC Pvt Ltd",
                        "total": 15000
                    }
                """

    assert fake_openai.responses.last_kwargs == {
        "model": "test-model",
        "input": "Extract invoice number",
    }


def test_openai_client_returns_invalid_json_as_raw_text():
    class InvalidJSONResponse:
        output_text = "this is not valid json"

    class InvalidJSONOpenAI:
        class responses:
            @staticmethod
            def create(**kwargs):
                return InvalidJSONResponse()

    client = OpenAIClient.__new__(OpenAIClient)
    client.client = InvalidJSONOpenAI()
    client.model = "test-model"

    result = client.generate("Extract invoice number")

    assert result == "this is not valid json"


def test_openai_client_propagates_api_error():
    class FailingOpenAI:
        class responses:
            @staticmethod
            def create(**kwargs):
                raise RuntimeError("LLM servive unavailable")

    client = OpenAIClient.__new__(OpenAIClient)
    client.client = FailingOpenAI()
    client.model = "test-model"

    try:
        client.generate("Extract invoice number")
    except RuntimeError as exc:
        assert str(exc) == "LLM servive unavailable"
    else:
        raise AssertionError("Expected RuntimeError")