from model_provider import generate_structured_response

import json
import re

# Everything ASTI knows how to do with a turn.
# Adding a capability = add it here, add a branch in llm.py's loop
# (later: a dedicated handler module).
INTENTS = {
    "chat",              # greetings, opinions, open-ended talk *about the user's own life/context*
    "recall",            # user is asking ASTI to retrieve a fact it already stored about them
    "general_knowledge", # a question with no personal angle — answered without personal memory
    "code",              # user wants a script/code written — same privacy boundary as
                          # general_knowledge (never loads personal memory), routed to cloud
                          # when allowed since the local model is unreliable at this (10/14)
}

# Deterministic override, checked before the LLM call. A message that
# explicitly references "this/that/the doc/document/file/pdf" is, by
# definition, asking about something in conversation history — never
# general_knowledge (never loads history) or recall (only checks structured
# personal facts, never conversation content). Caught a real failure:
# "what are the grc parts of this doc", asked immediately after a PDF
# upload, classified general_knowledge and got sent to Claude with zero
# context, which correctly replied "I don't see any document attached."
# Python enforces this — it's a clear, mechanical signal, not a judgment
# call worth re-litigating via prompt tuning.
_FILE_REFERENCE_RE = re.compile(
    r"\b(this|that|the)\s+(doc(ument)?|file|pdf)s?\b",
    re.IGNORECASE,
)

# Deterministic override, checked after the file-reference one (a request
# about an uploaded file needs its conversation-history context, which the
# cloud-bound "code" path never loads — file reference wins if both match).
# Catches the clearest "write me code" phrasings without waiting on the LLM
# classifier, same precedent as the file-reference regex above. Added 10/14
# after a real failure: llama3 fabricated an unrelated trivia question
# instead of writing a requested script (see PROJECT_LOG.md).
_CODE_REQUEST_RE = re.compile(
    r"\b(write|give|generate|create|make)\b.{0,20}\b(script|code|function|program|snippet)\b",
    re.IGNORECASE,
)

# Non-code uses of "program"/"script"/"code" that _CODE_REQUEST_RE would
# otherwise catch (stress test, 10/14): "create a treatment program for my
# client", "write a script for a role play where I confront my father",
# "give me the code of conduct". Each of those was routed to the cloud-bound
# "code" path. Vetoes the code override; the message falls through to the
# LLM classifier like any other.
_NON_CODE_RE = re.compile(
    r"\b(treatment|workout|training|exercise|rehab|therapy|recovery|meal|diet|"
    r"study|loyalty|rewards?|wellness|mentorship|degree|tv|radio)\s+program"
    r"|\brole[- ]?play"
    r"|\bscript\s+for\s+(a|an|my|the)\s+(role|call|conversation|session|meeting|"
    r"video|podcast|speech|presentation|play|scene|pitch|interview|talk)"
    r"|\b(sales|phone|call|video|movie|film|podcast|speech|interview)\s+script"
    r"|\bcode\s+of\s+(conduct|ethics|professional)"
    r"|\b(penal|tax|zip|postal|area|dress|promo|discount|building|bar|ethics|civil|criminal)\s+code",
    re.IGNORECASE,
)

# Sensitive-details guard (stress test, 10/14). The classifier's idea of
# "personal" is the user's OWN life, so a professional asking about a
# client/patient/employee reads as "not personal" -> general_knowledge/code
# -> cloud. That sent an SSN, a privileged client confession, a named
# patient's allergy, and a client's immigration status out in testing. A
# hit here forces the turn local ("chat") before the LLM classifier ever
# sees it — Python enforces the boundary, the model never decides it.
#
# Pattern-based on purpose (no model call): deterministic and auditable,
# but not exhaustive — it catches the common shapes, not every possible
# phrasing. False positives only cost answer quality (a local answer
# instead of a cloud one), never privacy, so the patterns lean broad.
_ROLE_WORDS = (
    r"(client|patient|customer|employee|staff member|plaintiff|defendant|"
    r"deponent|witness|tenant|counselee|claimant|beneficiary)s?"
)
_SENSITIVE_RES = [
    # "my client", "our patient", "her employee", "my other client"...
    # Possessives only — a bare "the client" is too common in plain
    # technical questions ("the client sends a SYN") to count.
    re.compile(rf"\b(my|our|his|her|their|another|other)\s+(\S+\s+){{0,3}}?{_ROLE_WORDS}\b", re.IGNORECASE),
    # Legal roles are sensitive with any article: "the defendant admitted..."
    re.compile(r"\b(the|this|that|a|an)\s+(plaintiff|defendant|deponent|opposing (party|counsel))\b", re.IGNORECASE),
    # "Patient John Kim", "Employee Tom Baker", "client Daniel Reyes"
    re.compile(rf"\b(?i:{_ROLE_WORDS})\s+[A-Z][a-z]+"),
    # Honorific + name: "Mrs. Patel", "Dr. Brooks"
    re.compile(r"\b(Mr|Mrs|Ms|Miss|Dr)\.?\s+[A-Z][a-z]+"),
    # Case captions: "Reyes v. Hartwell", "State v. Reyes" ("v." only —
    # "Python vs JavaScript" is not a lawsuit)
    re.compile(r"\b[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+"),
    # Identifiers: SSN, MRN, DOB, email, phone, account/routing numbers
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(ssn|social security( number)?|mrn|medical record( number)?|dob|date of birth|"
               r"account number|routing number|policy number|case number|docket)\b", re.IGNORECASE),
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    re.compile(r"\(?\b\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"),
    # Legal privilege / confidentiality signals
    re.compile(r"\b(privileged|attorney[- ]client|confidential|admitted to me|confessed|"
               r"told me (that )?(he|she|they)|disclosed|settlement (offer|floor|authority)|"
               r"undocumented|immigration status|arrested|indicted|charged with)\b", re.IGNORECASE),
    # The user's own health/legal/financial situation
    re.compile(r"\b(i was|i've been|i have been|i am|i'm|just got|got)\s+(just\s+)?"
               r"(diagnosed|prescribed|arrested|sued|fired|evicted|charged)\b", re.IGNORECASE),
    re.compile(r"\bmy\s+(diagnosis|symptoms?|lab( results)?|labs|test results|biopsy|scan|mri|"
               r"medications?|meds|prescription|therapist|psychiatrist|doctor|lawyer|attorney|"
               r"divorce|custody|debt|bankruptcy|tax return|salary|income|ssn)\b", re.IGNORECASE),
    re.compile(r"\b(tested positive|hiv|stds?|stis?|miscarriage|abortion|relapsed?|sober|"
               r"rehab|abus(e|ed|er|ive)|sexual(ly)? abus\w*|harass\w*|assaulted|lump)\b", re.IGNORECASE),
    # The user's family/relationships and money/housing trouble — personal
    # by definition, so local is the right place regardless.
    re.compile(r"\bmy\s+(wife|husband|spouse|partner|ex|son|daughter|kids?|child|children|mom|dad|"
               r"mother|father|brother|sister|boyfriend|girlfriend|landlord|boss|manager)\b", re.IGNORECASE),
    re.compile(r"\b(i|we)\s+owe\b|\b(behind|late)\s+on\s+(rent|my|our|the mortgage|payments)|\bevict", re.IGNORECASE),
    # Deal confidentiality / material non-public information
    re.compile(r"\b(merger|acquisition)\s+(talks|negotiations|target|before)|\binsider\b|"
               r"\bnon-?public\b|\bmnpi\b|\bnda\b", re.IGNORECASE),
    re.compile(r"\b(i'm|i am|she's|she is|my wife is|my partner is)\s+pregnant\b", re.IGNORECASE),
    # Business-internal numbers: "our revenue", "our payroll", "we owe the IRS"
    re.compile(r"\b(our|my company's|my business's)\s+(revenue|payroll|customers?|clients?|"
               r"invoices?|books|finances|employees|staff|taxes|cash flow|bank)\b", re.IGNORECASE),
]


def contains_sensitive_details(message):
    return any(r.search(message) for r in _SENSITIVE_RES)


def mentions_third_party(message):
    # Narrower than contains_sensitive_details: is this message about a
    # *specific other person* the user works with (a client, patient,
    # employee, "Mrs. Patel")? Used by llm.py to keep those facts out of the
    # user's own global personal memory, and to tell a therapist describing
    # a client apart from a user in crisis themselves.
    return any(r.search(message) for r in _SENSITIVE_RES[:4])


# A message has to actually be a question to be "recall" (stress test,
# 10/14): "My patient Maria Lopez, 54, has type 2 diabetes..." and
# "Remember that my client Sarah's next session is Thursday" were both
# classified recall and answered "I don't have that stored yet." A
# statement is never a lookup — Python enforces that, not the model.
_QUESTION_START_RE = re.compile(
    r"^\s*(what|whats|what's|why|how|when|where|who|whos|who's|which|whose|"
    r"do|does|did|are|is|was|were|can|could|would|should|will|tell me|remind me)\b",
    re.IGNORECASE,
)


def _is_question(message):
    m = message.strip()
    return m.endswith("?") or bool(_QUESTION_START_RE.match(m))


INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": sorted(INTENTS),
        }
    },
    "required": ["intent"],
}


def classify_intent(message, previous_message=None):
    # `previous_message`: the user's prior message in this conversation, if
    # any — shown to the classifier as context so a follow-up like "can he
    # still testify?" isn't classified as if it arrived with no history
    # (stress test, 10/14). The deterministic checks below never use it.
    if _FILE_REFERENCE_RE.search(message):
        return "chat"

    if contains_sensitive_details(message):
        return "chat"

    if _CODE_REQUEST_RE.search(message) and not _NON_CODE_RE.search(message):
        return "code"

    previous_block = (
        f"\nPrevious user message (context only, do not classify it):\n{previous_message}\n"
        if previous_message else ""
    )

    # Model interprets meaning; Python enforces the allowlist.
    # Bad JSON or an unknown label falls back to "chat" — never crash,
    # never route to a capability that doesn't exist.
    prompt = f"""You are an intent classifier for a personal assistant.
Classify the user's message into exactly one intent.

Intents:
- chat: conversation that involves the user's own life, preferences, goals,
  projects, or people — anything where knowing personal context about the
  user would help answer well. Includes the user telling the assistant
  something about themselves.
- recall: the user is explicitly asking the assistant to retrieve a fact it
  already stored about them, such as "what's my favorite color?",
  "what did I say my goal was?", "do you remember my brother's name?".
- general_knowledge: a factual, technical, or open-ended question that has
  nothing to do with the user's own life or stored facts — it would be
  answered the same way no matter who asked it. Examples: "what's the
  capital of France", "explain how TCP handshakes work", "what's a good
  rate limiting algorithm", "who won the world series in 1998".
- code: the user wants a script, program, or code snippet written for them,
  in any programming language. Examples: "write me a bash script that
  renames files", "can you code a function to reverse a string",
  "I need a python program that scrapes a webpage". Drafting letters,
  emails, contracts, NDAs, memos, or other prose is NOT code — that is chat
  (if it involves the user's own work, clients, or situation) or
  general_knowledge.

A follow-up that continues the previous message's topic (e.g. "can he still
testify?", "what about her dose?") belongs to the same kind of conversation
as that previous message. Anything about the user's clients, patients,
employees, customers, or business is chat, not general_knowledge.
{previous_block}
User message:
{message}

Return JSON matching the provided schema."""

    raw = generate_structured_response(prompt, INTENT_SCHEMA)

    try:
        intent = json.loads(raw).get("intent")
    except (json.JSONDecodeError, TypeError):
        return "chat"

    if intent not in INTENTS:
        return "chat"

    # Statements are never lookups (see _is_question).
    if intent == "recall" and not _is_question(message):
        return "chat"

    return intent
