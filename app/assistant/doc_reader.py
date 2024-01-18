



assistant_data = {
    "name": "document-reader", 
    "model": {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "systemPrompt": (
            "You're an AI assistant who helps users explore any document with the Document Id once selected. "
            "YOUR REPLY SHOULD NEVER CONTAIN DOCUMENT ID, only use the alias 'Document' instead "
            "(ONLY EXCEPTION IS THE FUNCTION CALL WHERE DOCUMENT ID can be passed.). "
            "Given a user query, create INTERMEDIATE QUESTIONS by expanding the query, "
            "taking into consideration the user's intention, type of query, required information, and so on. "
            "Then, call the corresponding functions that can help you answer the questions."
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
                        },
                        "doc_id": {
                            "type": "string",
                            "description": "The ID of the Document selected",
                        },
                    },
                    "required": ["query", "doc_id"],
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
