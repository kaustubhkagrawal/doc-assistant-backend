



assistant_data = {
    "name": "document-reader", 
    "model": {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "systemPrompt": (
            "You're an AI assistant who can create appropriate INTERMEDIATE QUERIES based on the user query. Then Call the appropriate function to get the answer of the user query if necessary."
        ),
        "functions": [
            {
                "name": "queryBook",
                "description": (
                    "Given any INTERMEDIATE QUESTIONS for the document, "
                    "this function can search the document for an appropriate response "
                    "and the sources from the Document."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "This is the DETAILED INTERMEDIATE QUESTION to search in THE DOCUMENT "
                                "based on the user query. This should be a valid question."
                            ),
                        }
                    },
                    "required": ["query"],
                },
            },
        ],
    },
    "voice": {
        "provider": "11labs",
        "voiceId": "paula",
    },
    "firstMessage": "Hi, I'm your Document reading assistant. You can ask me any question on Document",
}
