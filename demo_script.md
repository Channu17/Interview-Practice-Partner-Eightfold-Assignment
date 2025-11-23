# Demo Script (≤10 minutes)

## Segment 1 – Cold Open & Goal (0:00–0:45)
**Screen:** Dashboard landing page.  
**Voiceover:** “Hi, I’m walking you through our AI interview coach. Today I’ll show how it adapts to different personas and how the backend orchestrates every step.”

## Segment 2 – Architecture Snapshot (0:45–2:00)
**Screen:** Brief code peek at `backend/routes/interview.py` plus infra diagram sketch.  
**Voiceover:** “FastAPI routes handle session lifecycle. Resume text feeds `_ensure_resume_context`, providing custom prompts. We persist turns in MongoDB, while `llm.py` powers dynamic questioning and scoring.”

## Segment 3 – Persona A: Priya, Senior Python Dev (2:00–4:15)
**Screen:** Trigger `/start-interview` via UI or REST client with Priya’s profile.  
**Voiceover:** “Starting as Priya, a backend specialist. Notice the first question greets her by name—`_personalize_opening` stitches resume context and domain. I answer a technical prompt; FastAPI posts to `/process-answer`, appends history, and calls `generate_interview_question` for the next turn.”  
**Screen:** Show JSON response with next question + behavior tag.  
**Voiceover:** “Behavior cues highlight what the interviewer is probing—communication, system design, or leadership.”

## Segment 4 – Persona B: Jordan, Sales Strategist (4:15–6:45)
**Screen:** Switch persona form inputs.  
**Voiceover:** “Now Jordan, a revenue leader. Same flow, but prompts lean into sales metrics and negotiation scenarios because the resume context swaps domains. I give a behavioral answer; the agent requests a follow-up emphasizing stakeholder alignment.”

## Segment 5 – Error Handling & Persistence (6:45–7:45)
**Screen:** Show database document snapshot.  
**Voiceover:** “Each session tracks questions, answers, behaviors, and candidate name. Edge cases—invalid IDs, completed interviews—return clean HTTP errors to keep the UI predictable.”

## Segment 6 – Feedback Generation (7:45–9:00)
**Screen:** Trigger `/end-interview`, display feedback payload.  
**Voiceover:** “When I end the interview, `evaluate_interview` summarizes strengths and gaps. The UI renders this report, giving candidates actionable guidance immediately.”

## Segment 7 – Wrap (9:00–9:45)
**Screen:** Return to dashboard, highlight next steps button.  
**Voiceover:** “You’ve seen adaptive prompts across personas, resume-aware questioning, and automated scoring—all running inside our FastAPI stack. Thanks for watching.”
