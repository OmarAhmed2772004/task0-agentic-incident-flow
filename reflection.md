# Reflection — Task 0

## What was the hardest part?

The hardest part wasn't the application logic itself — it was the amount of
real-world infrastructure friction outside my control. My Python version
(3.14) had no prebuilt wheel for the pinned `pydantic` version, forcing a
switch to unpinned dependency versions. Then, during this exact project
window, Google was issuing new `AQ.`-prefixed Gemini API keys that were
rejected by the Gemini REST API across every Google account I tried (a
confirmed, widespread outage on Google's side) — I had to swap the whole
LLM provider to Groq mid-project, on a tight deadline. On top of that,
ServiceNow's Business Rule needed the "Insert" checkbox explicitly enabled
(easy to miss), and the resolution code value ("Solved (Permanently)")
that I expected from ServiceNow documentation didn't match my specific PDI's
actual choice list ("Solution provided") — I only found this by testing the
ServiceNow write-back directly with `Invoke-WebRequest` and reading the
exact error message ServiceNow returned, rather than guessing.

## What would you improve with more time?

I'd add a startup check that verifies the LLM key and ServiceNow
credentials both work *before* accepting webhook traffic, rather than
discovering a bad key only after a real incident silently fails in the
background. I'd also make the in-memory de-duplication persistent (e.g.
a small SQLite file) so it survives a service restart, add automatic
retries with backoff on both the LLM call and the ServiceNow write-back
instead of failing outright on the first transient network error, and
write a couple of unit tests for the prompt-building and decision-parsing
logic so future changes to `prompt.txt` don't silently break the JSON
contract.