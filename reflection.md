# Reflection — Task 0

## What was the hardest part?

The hardest part was connecting ServiceNow, the FastAPI webhook, ngrok, and the LLM into one reliable end-to-end flow. Setting up the ServiceNow Business Rule and making sure it could reach my local FastAPI server through ngrok required careful testing because the public endpoint can change when the tunnel is restarted. Another challenge was getting the LLM to consistently return a decision in a format that the application could parse and use safely. I also had to handle the incident processing asynchronously so that ServiceNow could receive a quick `202 Accepted` response while the LLM processing and ServiceNow write-back continued in the background. Finally, I had to adapt the LLM integration from Gemini to Groq while keeping the same decision logic and JSON contract.

## What would you improve with more time?

With more time, I would make the system more robust by adding persistent de-duplication instead of relying only on in-memory state. I would also add retries with exponential backoff for temporary failures from the LLM and ServiceNow APIs. The LLM output validation could be strengthened using structured output or a stricter schema instead of relying mainly on prompt-based JSON formatting. I would also add more automated unit and integration tests covering invalid payloads, API failures, duplicate incidents, and unexpected LLM responses. Finally, I would improve the logging and monitoring so that failures in the background processing are easier to diagnose without manually checking the server logs.
