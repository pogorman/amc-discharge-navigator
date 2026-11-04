"""Build the captioned, narrated demo video from O'G's beat recordings: the hero video's title card, the hero video's
overview, a card into the walkthrough, then each beat with a chapter card, a "what you'll see" card, the recording in a
branded frame, captions underneath and a speed badge wherever a wait is sped up. An AI voice reads the narration.

Inputs: the recordings in videos-do-not-put-in-repo/*.mp4 (gitignored; O'G keeps them on each laptop), two deck
slides as docs/demo-video/<slide name>.png (captured from deck.html; runbook.html#demo-video) and docs/assets/hero.mp4.
The voice comes from Azure Speech in the Foundry resource named in .env, signed in with the az account (no keys).
Output: docs/assets/demo-video.mp4, plus .vtt captions (the narration) next to it. Work files go to
videos-do-not-put-in-repo/build/. docs/deck.html follows the video slide for slide; every build checks it and writes
its card slides, times and narration.

Needs Pillow, NumPy and imageio-ffmpeg (a throwaway venv is fine). Run from the repo root:
  python scripts/build_demo_video.py            build everything
  python scripts/build_demo_video.py --only b3  rebuild one segment, then re-join
  python scripts/build_demo_video.py --review   contact sheets of the finished video at every caption
  python scripts/build_demo_video.py --deck     just bring deck.html into step with the last build
"""
import argparse, copy, hashlib, json, math, pathlib, re, shutil, subprocess, sys, time, urllib.error, urllib.request, wave
from html import escape
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "videos-do-not-put-in-repo"
STILLS, WORK = ROOT / "docs" / "demo-video", SRC / "build" / "work"
HERO = ROOT / "docs" / "assets" / "hero.mp4"
OUT = ROOT / "docs" / "assets" / "demo-video.mp4"
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1920, 1080, 30
WIN = (160, 22, 1600, 900)            # where the recording sits: x, y, width, height (16:9)
BAND_Y = 940                          # caption band, under the window
CARD_S, FADE_S = 2.6, 0.35

BG, TEXT, MUTED = (8, 17, 38), (243, 246, 251), (168, 181, 204)
TEAL, BLUE, AMBER = (63, 208, 187), (90, 169, 255), (255, 200, 92)
def font(name, size): return ImageFont.truetype("C:/Windows/Fonts/" + name, size)
REG, SEMI, BOLD, BLACK = "segoeui.ttf", "seguisb.ttf", "segoeuib.ttf", "seguibl.ttf"

# ---------------------------------------------------------------- the edit
# A crop is (x, y, width) in the recording's pixels (1872x1076); height follows at 16:9. FULL is the whole screen.
# Every part shows the whole window: O'G wants the native window at its own zoom, so viewers keep the context. No zooms.
FULL = (0, 12, 1872)
FULL_1908 = (16, 0, 1876)  # beat-3-new.mp4 is 1908x1056: only the blank margin either side goes

# A tour pauses a recording (or a slide) on one frame and walks through parts of the screen: the rest dims, a box glides
# to each part and a note beside it says what it is (O'G, 2026-11-03: "a square around each item" with text that says
# what it's for). Boxes are (x0, y0, x1, y1) in the recording's or the slide's pixels. A note goes on the first side
# where it fits (right, left, below, above) unless the step names one; a tag shows in amber next to the step number.
# A step's say is what the narrator says while its box is up; the step lasts long enough to read the note and hear it.
TOUR_IN, TOUR_OUT = 0.5, 0.6
def step(title, box, text, tag=None, side=None, say=None): return dict(title=title, box=box, text=text, tag=tag, side=side, say=say)
def step_s(s): return s.get("fit") or round(max(3.8, 1.6 + len(s["text"].split()) / 4.5), 1)  # fit: set by fit_all()
def tour_s(tour): return round(TOUR_IN + sum(step_s(s) for s in tour["steps"]) + TOUR_OUT, 2)

M365_TOUR = dict(caption="First, a look around **Microsoft 365 Copilot Chat**.", steps=[
    step("Work IQ", (356, 14, 456, 56), "Copilot's work context: your email, chats, meetings and files, through Microsoft Graph, with your permissions.", side="below",
         say="Work IQ is Copilot's work context: email, chats, meetings and files, through Graph, with the user's own permissions."),
    step("Auto", (464, 14, 546, 56), "The model picker. On Auto, Copilot picks the right model for each question.", side="below",
         say="The model picker is on Auto, so Copilot picks the right model for each question."),
    step("Chat, Cowork and Code", (24, 72, 316, 116), "We're in Microsoft 365 Copilot Chat. Cowork and Code, the other two modes, are a click away.", side="right",
         say="This is Copilot Chat. Cowork and Code, the other two modes, are a click away."),
    step("The left nav", (12, 132, 300, 462), "Start a new chat, search past ones, open the library, find agents and workspaces, and pick up recent chats.", side="right",
         say="On the left: new chats, search, the library, agents, and recent chats."),
    step("Our first prompt", (600, 498, 1625, 650), "In plain words: what's holding up Miguel Reyes's discharge, and what did I miss over email? Next, we send it.", side="above",
         say="And the first prompt, in plain words: what's holding up Miguel Reyes's discharge, and what did I miss over email?"),
])
ANSWER_TOUR = dict(caption="Where the answer came from: **the case manager's own email**.", steps=[
    step("The hold-up", (574, 326, 1616, 366), "The SNF insurance authorization, waiting on an updated PT note.", side="below",
         say="The hold-up: the skilled nursing facility's prior authorization, waiting on an updated PT note."),
    step("The payer's email", (596, 378, 1606, 486), "PA-2210-7734: the reviewer wants PT notes with ambulation distance and level of assist.", side="below",
         say="The payer wants PT notes with ambulation distance and level of assist. Remember that for chapter three."),
    step("Maple Grove's email", (596, 682, 1606, 756), "The SNF referral reply: they can take him tomorrow, once the authorization comes through.", side="above",
         say="And Maple Grove can take him tomorrow, once the authorization comes through."),
])
AGENTS_TOUR = dict(caption="Open **Agents & Skills**, then find **Discharge Navigator**.", steps=[  # beat-3-new.mp4
    step("Agents & Skills", (18, 212, 562, 638), "Every agent and skill you can use in Microsoft 365 Copilot, a click away: Microsoft's own and the ones your organization builds.", side="right",
         say="Agents and Skills lists what they can use here: Microsoft's own agents, and the ones their organization builds."),
    step("Discharge Navigator", (282, 494, 550, 532), "Built in Copilot Studio and published here. Same window, now with an agent that knows the discharge plan.", side="right",
         say="Discharge Navigator was built in Copilot Studio and published here, right where they already work."),
])
STUDIO_TOUR = dict(caption="A tour of the agent's setup, before anything changes.", steps=[
    step("Instructions", (104, 322, 1270, 1050), "Its job, in plain language: who it helps, where the data lives, and the rules it must follow.",
         say="The instructions give it its job in plain language: who it helps, where the data lives, and the rules it follows."),
    step("Channels", (1322, 186, 1842, 304), "Where people use it. This agent is published to Teams and Microsoft 365 Copilot.",
         say="Channels: it's published to Teams and Microsoft 365 Copilot."),
    step("Skills", (1322, 330, 1842, 498), "Recipes for two jobs: patient instructions and the prior-auth packet. Each reads the chart in Dataverse, then hands the writing to a model deployment in Microsoft Foundry (formerly Azure AI Foundry).",
         say="Skills are recipes for two jobs: patient instructions, and the prior-auth packet. Each one reads the chart in Dataverse, then hands the writing to a model deployment in Microsoft Foundry, formerly Azure AI Foundry."),
    step("Tools", (1322, 527, 1842, 646), "How it reaches other systems: Dataverse for the discharge plan, and the model deployments in Foundry for drafts.",
         say="Tools are how it reaches other systems: Dataverse for the plan, and the model deployments in Foundry for the drafts."),
    step("Knowledge", (1322, 672, 1842, 735), "Documents and sites it can search for answers. None here: the facts come from Dataverse.",
         say="There are no documents to search. The facts come from Dataverse."),
    step("Connected agents", (1322, 756, 1842, 820), "Other agents it can hand work to. None here; this one works on its own.",
         say="It could hand work to other agents. This one works on its own."),
    step("Memory", (1322, 834, 1842, 920), "Remembers preferences and work in progress across sessions. Switched off for this agent.", tag="Preview",
         say="And memory, in preview, is switched off for this agent."),
])
SPANISH_TOUR = dict(caption="It answered **in Spanish**. Here's why.", steps=[
    step("The hand-off", (448, 410, 830, 524), "The skill sent his chart to the patient-summary model deployment in Foundry: Mistral Large 3, in preview.", side="right",
         say="The skill sent his chart to the patient-summary model deployment: Mistral Large 3, in preview."),
    step("In Spanish", (436, 572, 1500, 800), "His chart lists Spanish as his preferred language, so the skill asks for his instructions in Spanish, in plain words he can follow at home.", side="above",
         say="It's in Spanish because his chart lists Spanish as his preferred language. So he gets instructions in plain words he can follow at home."),
])
PACKET_TOUR = dict(caption="It answers the payer's question **from his chart**.", steps=[
    step("From his chart", (452, 432, 1480, 504), "What the payer asked for in chapter 1, quoted from the chart, with the field it came from.", side="below",
         say="It answers the payer's question from chapter one, quoting his chart, with the field each fact came from."),
    step("What's still missing", (452, 670, 1480, 816), "It flags the gap: no dated, signed PT note yet. A draft for the case manager to finish, not a submission.", side="below",
         say="And it flags the gap: no dated, signed PT note yet. A draft for the case manager to finish, not a submission."),
])
DASH_TOUR = dict(caption="What the Command Center shows, **live from Dataverse**.", steps=[  # pro-code-new.mp4
    step("The house-wide numbers", (24, 162, 1748, 296), "Discharges expected today, patients medically ready but still here, open barriers, prior-auth turnaround and readmission risk.",
         say="Across the house: discharges expected today, patients medically ready but still here, open barriers, prior-auth turnaround, and readmission risk."),
    step("Where the barriers are", (24, 310, 1748, 588), "Open barriers by type, and avoidable bed-days by unit: where discharges are stuck.",
         say="Where the barriers are, by type, and the avoidable bed-days, by unit."),
    step("Every active plan", (24, 600, 1748, 1050), "Sorted by avoidable days, with open barriers and readmission risk. Select one for the detail.", side="above",
         say="And every active plan, sorted by avoidable days. Select one for the detail."),
])
PANEL_TOUR = dict(caption="Miguel's plan, with **no prior-auth packet yet**.", steps=[
    step("His plan", (1228, 26, 1862, 246), "DP-1001 on 6 East: his diagnosis, destination, payer, language and hospital course, from the plan of record in Dataverse.",
         say="His plan of record in Dataverse: diagnosis, destination, payer, language, and his hospital course."),
    step("Agent drafts", (1228, 264, 1862, 452), "Where the agent's drafts land: patient instructions and the prior-auth packet. No packet yet.",
         say="The agent's drafts land here. There's no prior-auth packet yet."),
    step("Tasks and barriers", (1228, 476, 1862, 1050), "Each with an owner, a due date and a status, and a button to mark it complete.",
         say="And his tasks and barriers, each with an owner, a due date and a status."),
])
MODEL_TOUR = dict(caption="Written by **gpt-5.5**, the prior-auth model deployment in Foundry.", steps=[
    step("Which model wrote it", (1246, 820, 1856, 884), "The response says so: gpt-5.5, the prior-auth model deployment in Foundry. A draft for the case manager, not submitted.",
         say="The same skill as in chapter three wrote it, with gpt-5.5, the prior-auth model deployment in Foundry. A draft, not submitted."),
])
SAVED_TOUR = dict(caption="**Draft**: saved by Discharge Navigator, for clinician review and signature.", steps=[
    step("Saved as a draft", (1236, 350, 1862, 424), "Saved by Discharge Navigator to his plan, marked Draft, for clinician review and signature.",
         say="Marked as a draft, saved by Discharge Navigator, for a clinician to review and sign."),
    step("The packet", (1236, 424, 1862, 1050), "Every fact cites the chart field or task it came from, as in chapter 3.",
         say="Every fact cites where it came from in his chart."),
])
APP_TOUR = dict(caption="She starts on **App (preview)** in Copilot Studio.", steps=[
    step("App (preview)", (1290, 350, 1590, 650), "Apps in Copilot Studio, in preview: describe the app you want in plain words, and Copilot Studio builds it.", side="left",
         say="She starts on App, in preview, in Copilot Studio: describe the app you want, in plain words, and it builds it."),
])
ARCH_TOUR = dict(caption="An agent, two models, a pro dev's app and a nurse manager's app, all on **the same rows**.", steps=[  # architecture.png
    step("Microsoft 365", (360, 56, 600, 508), "Where people already work: Teams and Microsoft 365 Copilot. Graph holds the case manager's mail and chats.",
         say="Microsoft 365 is where people already work: Teams and Copilot. Graph holds the case manager's mail and chats."),
    step("The agent", (638, 100, 1240, 404), "Discharge Navigator in Copilot Studio: instructions, two skills, and tools for Dataverse (as the signed-in user) and Foundry.", side="below",
         say="The agent, in Copilot Studio: instructions, two skills, and tools for Dataverse and Foundry."),
    step("Dataverse", (638, 438, 962, 692), "One copy of the discharge plan: patients, plans and tasks. Every app and the agent use the same rows.",
         say="Dataverse holds one copy of the discharge plan. The agent and every app use the same rows."),
    step("Apps on the same data", (980, 438, 1240, 692), "The pro developer's Command Center and the nurse manager's Barrier Tracker.",
         say="On those rows: the pro developer's Command Center, and the nurse manager's Barrier Tracker."),
    step("Azure", (1278, 56, 1602, 828), "API Management is the only door to the two model deployments in Foundry, and it signs in with its own identity: no keys.",
         say="In Azure, API Management is the only door to the two model deployments in Foundry. It signs in with its own identity, so there are no keys."),
    step("One solution", (638, 710, 1240, 812), "Everything ships as one solution in a Managed Environment, with your governance.", side="above",
         say="Everything ships as one solution, in a Managed Environment, under your governance."),
    step("One tenant", (362, 842, 1600, 880), "One Entra ID tenant across Microsoft 365, Power Platform and Azure.", side="above",
         say="And it's all one Entra ID tenant, across Microsoft 365, Power Platform and Azure."),
])

def part(a, b, x=1, crop=FULL, hold=0, tour=None):
    return dict(a=a, b=b, x=x, crop=crop, hold=tour_s(tour) if tour else hold, tour=tour)

def scroll(x, *spans, crop=FULL):
    """Parts for a scroll through a response, with the stops between scroll-wheel turns cut out (O'G, 2026-11-03).
    The spans are where the picture moves, measured from the recording."""
    return [part(a, b, x, crop) for a, b in spans]

CHAPTERS = {  # number: (title, where it happens, the demo script's theme, short label for the progress row)
    1: ("Graph recall", "Microsoft 365 Copilot", "Connected intelligence", "Recall"),
    2: ("The agent in Microsoft 365", "Discharge Navigator · Microsoft 365 Copilot", "Agents in the flow of work", "Agent"),
    3: ("Behind the scenes: how it's built", "Copilot Studio · Microsoft Foundry", "Instructions, skills, tools and models", "How it's built"),
    4: ("Pro dev", "Discharge Command Center · a Power Apps Code App", "Pro devs in their own tools", "Pro dev"),
    5: ("The huddle: close a barrier", "Barrier Tracker", "One plan, every app", "Huddle"),
    6: ("The reveal: she built it herself", "Apps in Copilot Studio (preview)", "Build for everyone", "Reveal"),
    7: ("One plan. Every app. One platform.", "How it fits together", "One platform", "Close"),
}

# After each chapter card, a card that says what you're about to see: headline, lines under it, the pieces involved.
# Chapter 5 says what Barrier Tracker is but keeps how it was made for the reveal.
BRIEFS = {
    1: ("Microsoft 365 Copilot, out of the box",
        ["Copilot Chat with Work IQ. No agent, nothing built yet.",
         "It answers from the case manager's own email and chats."],
        ["Microsoft 365 Copilot", "Work IQ", "Microsoft Graph"]),
    2: ("Now an agent built for the job",
        ["Discharge Navigator, made in Copilot Studio, in the same Copilot window.",
         "It reads the plan of record in Dataverse, as the signed-in user."],
        ["Copilot Studio agent", "Dataverse MCP server", "Microsoft 365 Copilot"]),
    3: ("Inside Copilot Studio: how it's built",
        ["A tour of the agent's setup, then two drafts from two models in Microsoft Foundry:",
         "patient instructions from Mistral Large 3, a prior-auth packet from gpt-5.5."],
        ["Copilot Studio", "Skills", "Microsoft Foundry"]),
    4: ("A pro developer's app, written in code",
        ["The Discharge Command Center: a Power Apps Code App built in React.",
         "The house-wide view, each patient's plan, and the agent saving a draft."],
        ["Power Apps Code App", "React", "Discharge Navigator", "Microsoft Foundry"]),
    5: ("The 6 East huddle board",
        ["Barrier Tracker: the nurse manager's board for the morning huddle,",
         "a web app on the same plan in Dataverse. Who built it, and how, comes next."],
        ["Barrier Tracker", "Dataverse"]),
    6: ("Her request, then the build",
        ["First, the request she typed, word for word.",
         "Then Apps in Copilot Studio (preview) building Barrier Tracker from it, sped up."],
        ["Apps in Copilot Studio (preview)", "Dataverse", "No code"]),
    7: ("How it all fits together",
        ["One Entra ID tenant, one discharge plan in Dataverse,",
         "and every piece you just saw working on the same rows."],
        ["Microsoft 365", "Copilot Studio", "Power Platform", "Azure"]),
}

# What the narrator says over each chapter card; it runs on into the "What you'll see" card, which waits for it.
CHAPTER_SAY = {
    1: "Chapter one. First, Microsoft 365 Copilot on its own: no agent, nothing built yet. It answers from the case manager's own email and chats.",
    2: "Chapter two: an agent built for the job. Discharge Navigator, made in Copilot Studio, reads the discharge plan in Dataverse, as the signed-in user.",
    3: "Chapter three: behind the scenes, in Copilot Studio. A tour of how the agent is built, then two drafts from two model deployments in Microsoft Foundry.",
    4: "Chapter four: a pro developer's app. The Discharge Command Center is a Power Apps code app, written in React, with the same agent built in. This time, it saves the prior-auth packet to the plan.",
    5: "Chapter five: the morning huddle on 6 East, run from Barrier Tracker, the nurse manager's board on the same plan.",
    6: "Chapter six: the reveal. Nobody filed a ticket for that board, and nobody wrote any code. First, the request she typed. Then the build, sped up.",
    7: "Chapter seven: how it all fits together. One Entra ID tenant, one discharge plan in Dataverse, and every piece you just saw, working on the same rows.",
}

# The card between the hero's overview and the beats: kicker, title, the lines under it.
NEXT = ("The details", "Now let's see it work.",
        ["Seven steps, from one question in Microsoft 365 Copilot", "to an app a nurse manager built herself."])
NEXT_S = 5.0

# The card after the title card: the use case and the solution, before the overview (O'G, 2026-11-03).
INTRO = dict(kicker="The use case", title="Discharge planning at academic medical centers", columns=[
    ("Who it's for", "Hospitals tied to a medical school, where patient care, teaching and research meet."),
    ("The problem", "Once a patient is medically ready, every extra day in a bed is avoidable. Prior-auth delays add more.")],
    solution=("The solution", "**Discharge Navigator**: an agent and apps on one discharge plan, so everyone sees what's blocking a discharge and clears it sooner."))

# The cast as a card of its own (O'G, 2026-11-03: the pasted slide "looks sloppy"). Each row is colored by where it runs,
# as in the hero video: Microsoft 365 teal, Copilot Studio and Power Platform purple, Azure blue.
PURPLE = (184, 150, 255)
CAST = dict(kicker="Meet the cast", title="Who's who", rows=[
    ("Case manager", "Microsoft 365 Copilot and Teams", "Asks where they already work.", TEAL),
    ("The assistant", "Discharge Navigator, an agent in Copilot Studio", "Finds what's blocking a discharge. Can't delete anything.", PURPLE),
    ("Two writers", "Two model deployments in Microsoft Foundry", "Draft patient instructions and prior-auth packets.", BLUE),
    ("The gatekeeper", "Azure API Management", "The only door to the writers. No keys.", BLUE),
    ("The record", "Dataverse", "One copy of the plan. Everyone works on the same rows.", PURPLE),
    ("The huddle board", "Barrier Tracker, built in Copilot Studio (preview)", "A nurse manager's app. No code.", PURPLE),
    ("The capacity dashboard", "Discharge Command Center, a Code App", "Leadership's house-wide view, built in React.", PURPLE)],
    patient="Our patient: **Miguel Reyes**. Medically ready, still in a hospital bed.",
    legend=[("Microsoft 365", TEAL), ("Copilot Studio and Power Platform", PURPLE), ("Azure", BLUE)])

def words(*texts): return sum(len(t.replace("**", "").split()) for t in texts)
INTRO_S = round(min(2 + words(INTRO["title"], *(c[1] for c in INTRO["columns"]), INTRO["solution"][1]) / 4.5, 15), 1)
CAST_S = 15.0

# A tag that floats over the window's top-right corner for a whole beat: logo (in docs/demo-video), product, line under it.
M365 = ("copilot-logo.png", "Microsoft 365 Copilot", "with Work IQ")
STUDIO = ("copilot-studio-logo.png", "Microsoft Copilot Studio", "agent in Microsoft 365 Copilot")

# Captions: (time, text). For a recording the time is in the recording's own seconds; for a slide, seconds from its start.
# **bold** turns teal. A leading "> " shows the line as a prompt.
# say: what the narrator says, (time, text) on the same clock as captions (a card's or video's from its start); a time
# of None follows the line before (use it for a line over a held last frame: a hold's own clock can't be stretched). Where a line needs more room, fit_all() makes it: a sped-up stretch plays slower, a
# frame holds longer, a card or slide stays up longer. The captions on screen stay as written.
# A video segment can hold its last frame (hold) and fade from or to the plate (fade_in, fade_out), in seconds.
SEGMENTS = [
    dict(key="open", video=HERO, start=25.6, end=28.5, hold=1.0, fade_in=0.35, fade_out=0.35,  # the hero's end card
         say=[(0.3, "Discharge Navigator. One plan, every app, one platform.")]),
    dict(key="intro", card="intro", say=[  # the use case and the solution
        (0.4, "Discharge planning, at an academic medical center. Once a patient is medically ready, every extra day in a bed is avoidable, and prior-auth delays add more."),
        (None, "Discharge Navigator puts an agent and apps on one discharge plan, so everyone sees what's blocking a discharge, and clears it sooner.")]),
    dict(key="hero", video=HERO, start=0, end=25.0, fade_out=0.5, say=[  # the overview, up to where Deploy & govern leaves
        (0.2, "Miguel is medically ready, but he's still in a bed."),
        (4.2, "Ask the agent what's blocking him, right where you already work."),
        (9.6, "It drafts the paperwork, for clinicians to review and sign."),
        (13.7, "And every app works from the same plan."),
        (18.0, "All of it runs in your own tenant, under your own guardrails.")]),
    dict(key="next", card="next", say=[(0.3, "Now let's see it work, in seven steps.")]),
    dict(key="cast", card="cast", say=[
        (0.4, "Meet the cast: a case manager; Discharge Navigator, the agent; two model deployments in Foundry that write the drafts, behind API Management; Dataverse, the one copy of the plan; and two apps on that plan."),
        (None, "Our patient: Miguel Reyes. Medically ready, still in a bed.")]),
    dict(key="b1", num=1, brand=M365, items=[
        dict(clip="beat-1-m365-copilot.mp4", parts=[
            part(0, 2.9, tour=M365_TOUR), part(2.9, 4.2), part(4.2, 8.6, 1.5), part(8.6, 13.4, tour=ANSWER_TOUR),
            part(13.4, 14.6), part(14.6, 19.6), part(19.6, 24.9, hold=0.8)],
         captions=[
            (0, "The case manager asks Microsoft 365 Copilot what's holding up **Miguel Reyes**."),
            (2.9, "It searches the case manager's email and chats through **Microsoft Graph**, with their permissions."),
            (8.6, "The hold-up: the **SNF prior authorization**. The payer wants an updated PT note."),
            (14.6, "Maple Grove's email: they can take him **tomorrow**, once the auth is approved."),
            (19.6, "And the payer's: send **ambulation distance and level of assist**.")],
         say=[
            (0.0, "We start in Microsoft 365 Copilot Chat."),
            (2.9, "Copilot searches the case manager's mail and chats through Graph."),
            (13.4, "Each point links to the email it came from: Maple Grove's reply, then the payer's."),
            (19.6, "So far, that's Copilot out of the box. Nothing has been built yet.")])]),
    dict(key="b2", num=2, brand=STUDIO, items=[
        # Re-recorded 2026-11-03 so it's about Miguel (O'G); the first take, beat-2-m365-copilot-navigator-agent.mp4, was Ruth.
        dict(clip="beat-3-new.mp4", parts=[
            part(0, 4.5, crop=FULL_1908, tour=AGENTS_TOUR), part(4.5, 8.3, 1.5, FULL_1908), part(8.3, 10.7, crop=FULL_1908),
            part(10.7, 30.0, 8, FULL_1908), part(30.0, 42.0, 3, FULL_1908), part(42.0, 47.2, crop=FULL_1908),
            part(47.2, 49.4, crop=FULL_1908), part(49.4, 66.3, 6, FULL_1908), part(66.3, 67.0, crop=FULL_1908),
            *scroll(1, (67.75, 68.25), (68.72, 69.0), (69.72, 69.97), (70.62, 70.9), crop=FULL_1908),
            part(70.9, 72.7, crop=FULL_1908, hold=2.0)],
         captions=[
            (0, "Now the agent built for this job, **Discharge Navigator**, inside Microsoft 365 Copilot."),
            (8.3, "> Which of my patients are medically ready for discharge, but still here?"),
            (30.0, "It reads Dataverse through the **Dataverse MCP server**, signed in as the user."),
            (42.0, "From the plan of record in **Dataverse**: five patients. **Miguel Reyes** has waited **2 days**."),
            (47.2, "> What's holding up Miguel's discharge?"),
            (66.3, "Three barriers: the **prior authorization**, the **SNF placement** and **transport**."),
            (74.6, "The main dependency: the **updated PT note** the payer asked for in chapter 1."),  # in the held last frame,
            (79.5, "It can read and update a plan. **Every tool that could delete is switched off.**")],  # with the narration
         say=[
            (0.0, "Same window. This time, the case manager opens Agents and Skills."),
            (8.3, "They ask: which of my patients are medically ready for discharge, but still here?"),
            (30.0, "It reads Dataverse through its MCP server, signed in as the user, so it sees only what they can see."),
            (42.0, "Five patients, from the plan of record in Dataverse. Miguel Reyes has waited two days."),
            (47.2, "Then: what's holding up Miguel's discharge?"),
            (66.3, "Three barriers: the prior authorization, the placement at Maple Grove, and transport."),
            (None, "The main dependency is the updated PT note the payer asked for in chapter one."),
            (None, "And it can read and update a plan, but every tool that could delete is switched off.")])]),
    dict(key="b3", num=3, items=[
        dict(clip="beat-3-in-copilot-studio.mp4", parts=[
            part(0, 2.0), part(2.0, 4.6), part(4.6, 8.6, 2), part(8.6, 10.0, tour=STUDIO_TOUR), part(10.0, 12.5),
            part(12.5, 19.8, 1.5), part(19.8, 28.6, 2), part(28.6, 33.5, 3), part(33.5, 37.0),
            part(37.0, 55.3, 4), part(55.3, 56.15, tour=SPANISH_TOUR),
            *scroll(1.5, (56.34, 57.0), (57.5, 59.03), (59.39, 60.4), (60.77, 61.85), (62.14, 63.01), (63.45, 64.39),
                    (64.83, 65.7), (66.13, 67.22), (68.16, 68.89)),
            part(68.89, 71.0),
            part(71.0, 74.0, 2), part(74.0, 79.6, 2), part(79.6, 80.6, hold=3.0),
            *scroll(1.5, (81.51, 82.45), (83.25, 84.12), (84.91, 85.71), (86.15, 87.09), (87.6, 88.83), (88.83, 89.7)),
            part(90.13, 91.0, 1.5, tour=PACKET_TOUR),
            *scroll(1.5, (91.29, 92.09), (92.53, 93.25), (93.69, 94.49), (94.99, 95.65), (96.15, 96.88), (97.17, 97.89),
                    (98.26, 98.98), (99.34, 100.14), (100.43, 101.23), (101.74, 102.53), (102.9, 103.77)),
            part(103.77, 104.2, hold=0.8)],
         captions=[
            (0, "Behind the agent: **Copilot Studio**, where it's built. Open Agents, then Discharge Navigator."),
            (10.0, "Then **a choice of model** for the agent itself, picked from a list."),
            (19.8, "**Publish** once, and it's live in Teams and Microsoft 365 Copilot."),
            (28.6, "> Draft Miguel Reyes's patient instructions"),
            (37.0, "A **skill** reads his chart in Dataverse, then hands the writing to a model in **Foundry**."),
            (56.34, "In plain words: his medicines, his next steps and **teach-back questions**."),
            (66.13, "Written by **Mistral Large 3** (preview). It's a draft his nurse reviews and signs."),
            (71.0, "> Build the SNF prior-auth packet for Miguel Reyes"),
            (79.8, "A different job, a different model: **gpt-5.5**. A draft for the case manager. Nothing is sent."),
            (91.29, "Every fact cites the chart field it came from, and **it asks before saving** anything.")],
         say=[
            (0.0, "This is Copilot Studio, where the agent is built. Open Agents, then Discharge Navigator."),
            (10.0, "Then a choice of model for the agent itself, picked from a list."),
            (19.8, "Publish once, and it's live in Teams and Microsoft 365 Copilot."),
            (28.6, "Now: draft Miguel Reyes's patient instructions."),
            (37.0, "A skill reads his chart in Dataverse, then hands the writing to a model deployment in Foundry."),
            (56.34, "His medicines, his next steps, and teach-back questions."),
            (66.13, "It's a draft his nurse reviews and signs."),
            (71.0, "Next, the prior-auth packet for the payer."),
            (79.8, "A different job, so a different model: gpt-5.5. It's a draft for the case manager. Nothing is sent."),
            (91.29, "And it asks before saving anything to his plan.")])]),
    dict(key="b4", num=4, items=[
        # Re-recorded 2026-11-03 (O'G): more of the app, and the agent drafting and saving the prior-auth packet. The first
        # take, beat-5-agent-in-code-app.mp4, was made after the bed acceptance closed and showed two barriers.
        dict(clip="pro-code-new.mp4", parts=[
            part(0, 2.6, crop=FULL_1908, tour=DASH_TOUR), part(2.6, 11.0, crop=FULL_1908, tour=PANEL_TOUR),
            part(11.0, 12.6, crop=FULL_1908), part(12.6, 16.6, 2, FULL_1908), part(16.6, 20.6, crop=FULL_1908),
            part(20.6, 49.4, 8, FULL_1908), part(49.4, 52.6, crop=FULL_1908), part(52.6, 54.6, crop=FULL_1908),
            part(54.6, 153.2, 20, FULL_1908), part(153.2, 155.25, crop=FULL_1908, tour=MODEL_TOUR),
            *scroll(1, (155.35, 155.75), (155.95, 156.25), (156.45, 156.75), (156.95, 157.35), (157.65, 158.15),
                    (158.75, 159.05), (159.65, 159.95), crop=FULL_1908),
            part(159.95, 162.3, crop=FULL_1908), part(162.3, 165.2, 1.5, FULL_1908), part(165.2, 169.0, crop=FULL_1908),
            part(169.0, 170.6, crop=FULL_1908, tour=SAVED_TOUR), part(170.6, 170.85, crop=FULL_1908, hold=1.0)],
         captions=[
            (0, "Leadership's house-wide view: the **Command Center**, a Power Apps Code App built in React."),
            (2.6, "Select a patient for **his whole plan**: his chart, the agent's drafts, his tasks and barriers."),
            (16.6, "The same agent, built into the app: **“What's still blocking Miguel Reyes?”**"),
            (49.4, "Three barriers, from his plan: the **prior authorization**, the **SNF placement** and **transport**."),
            (52.6, "> Draft his prior auth packet and save it to his record."),
            (159.95, "This time it **saves the draft to his record**. Nothing is submitted."),
            (162.3, "Back in the app, the packet is on his plan: **the same row** the agent just wrote."),
            (170.6, "One plan in Dataverse: this dashboard, the agent and every other app see **the same rows**.")],
         say=[
            (0.0, "This is leadership's house-wide view of discharges: the Command Center, a code app a pro developer built in React."),
            (2.6, "Select Miguel, and his whole plan opens: his chart, the agent's drafts, and his tasks and barriers."),
            (16.6, "The same agent is built into the app. What's still blocking Miguel Reyes?"),
            (49.4, "Three barriers: the prior authorization, the placement at Maple Grove, and transport."),
            (52.6, "Then: draft his prior-auth packet, and save it to his record."),
            (159.95, "And this time it saves the draft to his record."),
            (162.3, "Back in the app, the packet is on his plan."),
            (170.6, "One plan in Dataverse: this dashboard, the agent and every other app see the same rows.")])]),
    dict(key="b5", num=5, items=[
        dict(clip="beat-4-barrier-tracker-add-note-closeout.mp4", parts=[
            part(6.5, 9.3), part(9.3, 14.8), part(14.8, 19.3, 1.5), part(19.3, 24.2), part(24.2, 25.7, hold=1.8)],
         captions=[
            (6.5, "The 6 East nurse manager runs the morning huddle from her board: **Barrier Tracker**."),
            (9.3, "Maple Grove has accepted Miguel. She adds the note, right on the barrier."),
            (19.3, "Then marks the bed acceptance **completed**."),
            (23.6, "Off the board: **9 open barriers become 8**.")],
         say=[
            (6.5, "The 6 East nurse manager runs the morning huddle from her board."),
            (10.8, "Maple Grove has accepted Miguel, so she adds a note, right on the barrier."),
            (19.3, "Then marks the bed acceptance completed."),
            (23.6, "Nine open barriers become eight. It's the same row the agent and the Command Center read.")])]),
    dict(key="b6", num=6, items=[
        dict(img="prompt.png", dur=5, captions=[
            (0, "The reveal: **she built Barrier Tracker herself**, from this one request.")],
         say=[
            (0.3, "The reveal: she built Barrier Tracker herself, from this one request."),
            (None, "Plain language: what the huddle needs to see, the tables it should use, and that nobody can delete anything.")]),
        dict(clip="creating-mgd-runtime-barrier-tracker.mp4", parts=[  # 20.0 to 27.4 is the og-svc question, cut (O'G)
            part(0, 0.5, tour=APP_TOUR), part(0.5, 3.5, 1.5), part(3.5, 7.0), part(7.0, 20.0, 5),
            part(27.4, 58.0, 8), part(58.0, 60.8, 1.5), part(60.8, 68.0),
            part(68.0, 76.8, 6), part(76.8, 78.7, hold=1.2), part(78.7, 83.0, hold=4.5)],
         captions=[
            (3.5, "She pastes it into **Apps in Copilot Studio** (preview): her board, in her own words."),
            (7.0, "It finds the Discharge tables the hospital already has in **Dataverse**."),
            (27.4, "It builds the app, checks a live read, and publishes it."),
            (60.8, "**Real hospital data**, not made-up data: 6 East's open discharge barriers."),
            (68.0, "Published. It reads the data **as her**, so it can't see anything she couldn't already."),
            (78.8, "Barrier Tracker, the board from the huddle. **No code.**"),
            (83.0, "Even if you know nothing about building apps, **you can describe one**.")],
         say=[
            (3.5, "She pastes her request into Apps in Copilot Studio."),
            (7.0, "It finds the hospital's discharge tables in Dataverse, builds the app, checks a live read, and publishes it."),
            (60.8, "This is real hospital data: 6 East's open discharge barriers."),
            (65.0, "And it reads that data as her, so it can't see anything she couldn't already see."),
            (78.8, "And there's Barrier Tracker, the board from the huddle. No code."),
            (83.0, "Even if you know nothing about building apps, you can describe one.")])]),
    dict(key="b7", num=7, items=[
        dict(img="architecture.png", dur=4, tour=ARCH_TOUR, captions=[
            (0, "**One discharge plan** in Dataverse, one Entra ID tenant, one set of governance.")],
         say=[(0.3, "One discharge plan, one tenant, one set of governance.")])]),
    dict(key="end", video=HERO, start=25.6, end=28.5, hold=1.0, fade_in=0.35, say=[
        (0.3, "One plan. Every app. One platform."),
        (None, "The voice you've heard is Grant, from Microsoft's MAI-Voice-2.1 model, in preview in Azure Speech.")]),
]

# ---------------------------------------------------------------- drawing
# Text is drawn as a mask and filled with a solid color, so transparent layers keep clean edges.
def paint(img, xy, text, f, color, spacing=0.0, alpha=255):
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    x, y = xy
    if spacing:
        for ch in text:
            d.text((x, y), ch, font=f, fill=alpha)
            x += f.getlength(ch) + spacing
    else:
        d.text((x, y), text, font=f, fill=alpha)
        x += f.getlength(text)
    layer = Image.new("RGBA", img.size, tuple(color[:3]) + (255,))
    layer.putalpha(mask)
    img.alpha_composite(layer)
    return x

def shapes(img, draw):
    """Draw shapes on their own layer, then composite it."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw(ImageDraw.Draw(layer))
    img.alpha_composite(layer)

def spaced_len(text, f, spacing): return sum(f.getlength(ch) + spacing for ch in text) - spacing

def radial(cx, cy, rx, ry, stop):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
    return np.clip(1 - r / stop, 0, 1)[..., None]

_plate = None
def plate():
    """The hero video's background: navy, two color washes, two soft glows and a faint grid."""
    global _plate
    if _plate is None:
        img = np.zeros((H, W, 3), np.float32) + BG
        for cx, cy, rx, ry, col in [(0.9 * W, 0.9 * H, 1000, 700, (42, 26, 92)), (0.15 * W, 0.1 * H, 1200, 800, (19, 48, 107))]:
            a = radial(cx, cy, rx, ry, 0.6)
            img = img * (1 - a) + np.array(col, np.float32) * a
        glow = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(glow)
        d.ellipse([-150, 420, 550, 1120], fill=(29, 111, 214))
        d.ellipse([W + 120 - 600, -160, W + 120, 440], fill=(106, 63, 209))
        g = np.asarray(glow.filter(ImageFilter.GaussianBlur(80)), np.float32) * 0.35
        img = img + g * (1 - img / 255)
        grid = np.zeros((H, W), np.float32)
        grid[::64, :] = 1
        grid[:, ::64] = 1
        a = (grid * radial(W / 2, H / 2, 1101, 1101, 0.75)[..., 0] * 0.07)[..., None]
        img = img * (1 - a) + np.array(TEXT, np.float32) * a
        img += np.random.default_rng(7).uniform(-0.6, 0.6, img.shape)  # dither, so the washes don't band
        _plate = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    return _plate.copy()

def hole_alpha(box, radius, ss=3):
    """Alpha for the chrome: opaque everywhere except an anti-aliased rounded window."""
    m = Image.new("L", (W * ss, H * ss), 255)
    x, y, w, h = [v * ss for v in box]
    ImageDraw.Draw(m).rounded_rectangle([x, y, x + w - 1, y + h - 1], radius * ss, fill=0)
    return m.resize((W, H), Image.LANCZOS)

def progress(img, x_right, y, current):
    n, bw, gap = len(CHAPTERS), 30, 6
    x0 = x_right - n * bw - (n - 1) * gap
    def draw(d):
        for k in range(1, n + 1):
            x = x0 + (k - 1) * (bw + gap)
            col = TEAL + (255,) if k == current else (255, 255, 255, 115 if current and k < current else 40)
            d.rounded_rectangle([x, y, x + bw, y + 4], 2, fill=col)
    shapes(img, draw)

def chrome(seg):
    """The background with a rounded window cut out for the recording, the beat's kicker and the progress row."""
    img = plate()
    x, y, w, h = WIN
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([x, y + 14, x + w, y + h + 14], 18, fill=(0, 0, 0, 150))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(22)))
    shapes(img, lambda d: d.rounded_rectangle([x - 2, y - 2, x + w + 1, y + h + 1], 18, outline=(255, 255, 255, 55), width=2))
    num = seg.get("num")
    xk = paint(img, (x, 944), f"{num:02d}", font(BOLD, 18), TEAL, 3.5) + 14 if num else x
    paint(img, (xk, 944), (CHAPTERS[num][0] if num else seg["kicker"]).upper(), font(SEMI, 18), MUTED, 3.5)
    progress(img, x + w, 952, num)
    fine, ff = "Synthetic data · recorded in a demo tenant · narrated by an AI voice (MAI-Voice-2.1, preview)", font(REG, 15)
    paint(img, (x + w - ff.getlength(fine), 1050), fine, ff, MUTED, alpha=150)
    img.putalpha(hole_alpha(WIN, 16))
    return img

def runs(text):
    """Split **bold** markup into (text, is_bold) runs."""
    return [(chunk, k % 2 == 1) for k, chunk in enumerate(text.split("**")) if chunk]

def caption_png(text, path):
    """One caption line for the band (1920x140, transparent), shrunk until it fits the window's width."""
    prompt = text.startswith("> ")
    shown = f"“{text[2:]}”" if prompt else text
    tf = font(BOLD, 15)
    tag_w = spaced_len("PROMPT", tf, 2.5) + 26
    for size in range(34, 27, -1):
        reg, bold = font(SEMI, size), font(BOLD, size)
        width = (tag_w + 16 if prompt else 0) + sum((bold if b else reg).getlength(t) for t, b in runs(shown))
        if width <= WIN[2]:
            break
    else:
        sys.exit(f"Caption too long for one line: {text}")
    img = Image.new("RGBA", (W, 140), (0, 0, 0, 0))
    x, y = WIN[0], 34
    if prompt:
        shapes(img, lambda d: d.rounded_rectangle([x, y + 7, x + tag_w, y + size + 5], 8, fill=BLUE + (45,), outline=BLUE + (200,), width=2))
        paint(img, (x + 13, y + 7 + (size - 2 - 19) / 2), "PROMPT", tf, BLUE, 2.5)
        x += tag_w + 16
    for t, b in runs(shown):
        x = paint(img, (x, y), t, bold if b else reg, TEAL if b else TEXT)
    img.save(path)

def badge_png(speed, path):
    """An amber pill, right-aligned in a 220x40 image: "6x SPEED", or "PAUSED" while a tour holds the recording."""
    img = Image.new("RGBA", (220, 40), (0, 0, 0, 0))
    paused = speed == "pause"
    label, f = "PAUSED" if paused else f"{speed:g}× SPEED", font(BOLD, 15)
    x0 = 220 - (16 + 22 + 8 + spaced_len(label, f, 2.5) + 16)
    def draw(d):
        d.rounded_rectangle([x0, 4, 219, 36], 16, fill=AMBER + (40,), outline=AMBER + (210,), width=2)
        for k in (0, 1):  # pause bars, or a fast-forward icon
            tx = x0 + 16 + k * 10
            if paused:
                d.rectangle([tx + 1, 13, tx + 5, 27], fill=AMBER + (255,))
            else:
                d.polygon([(tx, 13), (tx + 11, 20), (tx, 27)], fill=AMBER + (255,))
    shapes(img, draw)
    paint(img, (x0 + 46, 10), label, f, AMBER, 2.5)
    img.save(path)

def brand_png(brand, path):
    """The product tag, with room around it for its shadow. Returns where it goes: hanging off the window's top-right corner."""
    logo_file, name, sub = brand
    nf, sf, lh, pad = font(BOLD, 22), font(SEMI, 13), 40, 30
    logo = Image.open(STILLS / logo_file).convert("RGBA")
    logo = logo.resize((round(logo.width * lh / logo.height), lh), Image.LANCZOS)
    w, h = round(16 + logo.width + 13 + max(nf.getlength(name), spaced_len(sub.upper(), sf, 2.6)) + 22), 62
    img = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([pad, pad + 6, pad + w, pad + h + 6], 16, fill=(0, 0, 0, 160))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)))
    shapes(img, lambda d: d.rounded_rectangle([pad, pad, pad + w - 1, pad + h - 1], 16, fill=(14, 27, 58, 245), outline=(255, 255, 255, 60), width=1))
    img.alpha_composite(logo, (pad + 16, pad + (h - lh) // 2))
    tx = pad + 16 + logo.width + 13
    paint(img, (tx, pad + 8), name, nf, TEXT)
    paint(img, (tx + 1, pad + 38), sub.upper(), sf, TEAL, 2.6)
    img.save(path)
    # Its top overhangs the window's; its bottom (y 66) stays above the first line of content in the recordings.
    return WIN[0] + WIN[2] + 36 - w - pad, 4 - pad

def wrap(text, f, width):
    """Break text into lines no wider than width."""
    lines, line = [], ""
    for word in text.split():
        if line and f.getlength(f"{line} {word}") > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]

NOTE_W, NOTE_M = 480, 16  # a tour note's width, and the margin around it for its shadow
def note_png(n, total, s):
    """A tour note on a navy card like the product tag: which step, the part's name and what it's for."""
    pad, kf, tf, bf = 22, font(SEMI, 14), font(BOLD, 28), font(REG, 21)
    body = wrap(s["text"], bf, NOTE_W - 2 * pad)
    w, h, m = NOTE_W, 84 + 30 * len(body) + 12, NOTE_M
    img = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([m, m + 5, m + w, m + h + 5], 14, fill=(0, 0, 0, 150))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(8)))
    shapes(img, lambda d: d.rounded_rectangle([m, m, m + w - 1, m + h - 1], 14, fill=(14, 27, 58, 245), outline=(255, 255, 255, 60), width=1))
    x = paint(img, (m + pad, m + 16), f"{n} OF {total}", kf, TEAL, 2.6)
    if s["tag"]:
        paint(img, (x + 14, m + 16), s["tag"].upper(), kf, AMBER, 2.6)
    paint(img, (m + pad, m + 38), s["title"], tf, TEXT)
    for j, line in enumerate(body):
        paint(img, (m + pad, m + 82 + 30 * j), line, bf, (214, 222, 235))
    return img

def place(box, nw, nh, side, w, h):
    """Where a note goes beside its box: the step's side, or the first one where it fits on screen."""
    x0, y0, x1, y1 = box
    def at(side):
        if side in ("right", "left"):  # level with the box
            return (x1 + 26 if side == "right" else x0 - 26 - nw), (y0 + y1 - nh) / 2
        nx = x1 - nw if x1 - x0 > nw else x0  # under or over a wide box, at its right end
        return nx, (y1 + 22 if side == "below" else y0 - 22 - nh)
    def fits(p): return 16 <= p[0] <= w - nw - 16 and 16 <= p[1] <= h - nh - 16
    p = at(side) if side else next((at(s) for s in ("right", "left", "below", "above") if fits(at(s))), at("above"))
    return min(max(p[0], 16), w - nw - 16), min(max(p[1], 16), h - nh - 16)

def tour_painter(pc):
    """Set up a tour on its paused frame (of a recording, or a slide), at the window's size. Returns a function that
    draws it t seconds in."""
    tour, w, h = pc["paused"], WIN[2], WIN[3]
    if "img" in pc:
        im = Image.open(pc["img"]).convert("RGB")
        cx, cy, kx, ky = 0, 0, w / im.width, h / im.height
        base = im.resize((w, h), Image.LANCZOS).convert("RGBA")
    else:
        cx, cy, cw = pc["crop"]
        kx = ky = w / cw
        raw = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-ss", str(pc["at"]), "-i", str(pc["src"]), "-frames:v", "1",
                              "-vf", f"crop={cw}:{round(cw * 9 / 16 / 2) * 2}:{cx}:{cy},scale={w}:{h}:flags=lanczos",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        base = Image.frombytes("RGB", (w, h), raw).convert("RGBA")
    steps = tour["steps"]
    boxes = [((x0 - cx) * kx, (y0 - cy) * ky, (x1 - cx) * kx, (y1 - cy) * ky) for x0, y0, x1, y1 in (s["box"] for s in steps)]
    notes = []
    for i, (s, box) in enumerate(zip(steps, boxes)):
        img = note_png(i + 1, len(steps), s)
        nx, ny = place(box, img.width - 2 * NOTE_M, img.height - 2 * NOTE_M, s["side"], w, h)
        notes.append((img, round(nx) - NOTE_M, round(ny) - NOTE_M))
    starts, t = [], TOUR_IN
    for s in steps:
        starts.append(t)
        t += step_s(s)
    total, ss = tour_s(tour), 2  # the dimming and the box are drawn at twice the size, for smooth edges

    def at(t):
        i = max(j for j, s in enumerate(starts) if s <= max(t, TOUR_IN))
        end = starts[i + 1] if i + 1 < len(starts) else total - TOUR_OUT
        shown = ease(t / TOUR_IN) * (1 - ease((t - (total - TOUR_OUT)) / TOUR_OUT))
        if i:  # glide from the last part to this one
            p = ease((t - starts[i]) / 0.55)
            box = [a + (b - a) * p for a, b in zip(boxes[i - 1], boxes[i])]
        else:  # settle onto the first part
            grow = 40 * (1 - ease(t / TOUR_IN))
            box = [boxes[0][0] - grow, boxes[0][1] - grow, boxes[0][2] + grow, boxes[0][3] + grow]
        r = [v * ss for v in box]
        over = Image.new("RGBA", (w * ss, h * ss), BG + (round(150 * shown),))
        d = ImageDraw.Draw(over)
        d.rounded_rectangle(r, 12 * ss, fill=(0, 0, 0, 0))
        g = 8 * ss  # a soft teal ring just outside the box, then the box itself
        d.rounded_rectangle([r[0] - g, r[1] - g, r[2] + g, r[3] + g], 12 * ss + g, outline=TEAL + (round(90 * shown),), width=6 * ss)
        d.rounded_rectangle(r, 12 * ss, outline=TEAL + (round(255 * shown),), width=3 * ss)
        frame = base.copy()
        frame.alpha_composite(over.resize((w, h), Image.BOX))
        p_in = ease((t - starts[i] - (0.3 if i else 0.15)) / 0.35)
        alpha = p_in * (1 - ease((t - (end - 0.25)) / 0.25)) * shown
        if alpha > 0:
            img, nx, ny = notes[i]
            lay = img.copy()
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
            frame.alpha_composite(lay, (nx, ny + round(14 * (1 - p_in))))
        return frame
    return at

def gradient_text(text, f):
    """Text filled with the cover's blue, purple and teal gradient."""
    _, _, r, b = f.getbbox(text)
    mask = Image.new("L", (r, b), 0)
    ImageDraw.Draw(mask).text((0, 0), text, font=f, fill=255)
    yy, xx = np.mgrid[0:b, 0:r].astype(np.float32)
    k = np.clip((xx / r + yy / b) / 2, 0, 1)[..., None]
    c0, c1, c2 = (np.array(c, np.float32) for c in ((47, 111, 224), (106, 79, 216), (63, 208, 187)))
    col = np.where(k < 0.5, c0 + (c1 - c0) * (k / 0.5), c1 + (c2 - c1) * ((k - 0.5) / 0.5))
    img = Image.fromarray(col.astype(np.uint8)).convert("RGBA")
    img.putalpha(mask)
    return img

def ease(p): return 1 - (1 - min(max(p, 0), 1)) ** 3

def card_layers(num):
    """A chapter card: number, where, title and theme, over the chapter row with this one lit."""
    title, where, theme, _ = CHAPTERS[num]
    layers = [(gradient_text(f"{num:02d}", font(BLACK, 230)), 172, 170, 0.0)]  # (image, x, y, appears at)
    k = Image.new("RGBA", (1600, 40), (0, 0, 0, 0))
    paint(k, (0, 0), where.upper(), font(SEMI, 24), TEAL, 5)
    layers.append((k, 180, 470, 0.12))
    t = Image.new("RGBA", (1600, 120), (0, 0, 0, 0))
    paint(t, (0, 0), title, font(BOLD, 84 if font(BOLD, 84).getlength(title) < 1560 else 70), TEXT)
    layers.append((t, 176, 515, 0.22))
    cf = font(REG, 26)
    cw = int(cf.getlength(theme)) + 66
    c = Image.new("RGBA", (cw + 2, 56), (0, 0, 0, 0))
    shapes(c, lambda d: (d.rounded_rectangle([0, 0, cw, 54], 27, fill=(255, 255, 255, 18), outline=(255, 255, 255, 45), width=1),
                         d.ellipse([22, 21, 34, 33], fill=TEAL + (255,))))
    paint(c, (46, 11), theme, cf, TEXT)
    layers.append((c, 180, 660, 0.4))
    layers.append((chapter_row(num), 0, 950, 0.0))
    return layers

def chapter_row(num):
    """The chapter row along the bottom of a card, with this chapter lit."""
    p = Image.new("RGBA", (W, 60), (0, 0, 0, 0))
    def bars(d):
        for n in CHAPTERS:
            x = 180 + (n - 1) * 226
            d.rounded_rectangle([x, 0, x + 200, 4], 2, fill=TEAL + (255,) if n == num else (255, 255, 255, 115 if n < num else 40))
    shapes(p, bars)
    for n, (_, _, _, short) in CHAPTERS.items():
        paint(p, (180 + (n - 1) * 226, 18), f"{n:02d} {short}".upper(), font(SEMI, 18), TEXT if n == num else MUTED, 2.5,
              alpha=255 if n == num else 150)
    return p

def brief_layers(num):
    """The card after a chapter card: what you're about to see, and the pieces involved."""
    head, lines, pieces = BRIEFS[num]
    k = Image.new("RGBA", (1600, 40), (0, 0, 0, 0))
    paint(k, (0, 0), "WHAT YOU'LL SEE", font(SEMI, 24), TEAL, 5)
    size = next(sz for sz in range(76, 50, -2) if font(BOLD, sz).getlength(head) <= 1570)
    t = Image.new("RGBA", (1600, 110), (0, 0, 0, 0))
    paint(t, (0, 0), head, font(BOLD, size), TEXT)
    s = Image.new("RGBA", (1600, 54 * len(lines) + 12), (0, 0, 0, 0))
    for j, line in enumerate(lines):
        paint(s, (0, 54 * j), line, font(REG, 36), TEXT)
    layers = [(k, 180, 340, 0.0), (t, 174, 385, 0.12), (s, 180, 510, 0.3)]
    cf, x = font(REG, 26), 180
    for j, piece in enumerate(pieces):  # pills like the chapter card's theme
        cw = int(cf.getlength(piece)) + 66
        c = Image.new("RGBA", (cw + 2, 56), (0, 0, 0, 0))
        shapes(c, lambda d: (d.rounded_rectangle([0, 0, cw, 54], 27, fill=(255, 255, 255, 18), outline=(255, 255, 255, 45), width=1),
                             d.ellipse([22, 21, 34, 33], fill=TEAL + (255,))))
        paint(c, (46, 11), piece, cf, TEXT)
        layers.append((c, x, 690, 0.55 + 0.1 * j))
        x += cw + 16
    layers.append((chapter_row(num), 0, 950, 0.0))
    return layers

def brief_s(num):
    """Long enough to read the headline and lines at about 4.5 words a second."""
    head, lines, _ = BRIEFS[num]
    return round(min(max(1.5 + len(" ".join([head, *lines]).split()) / 4.5, 5.0), 8.0), 1)

def next_layers(card):
    """The card into the walkthrough: kicker, title and lines, then every chapter in the row lights up in turn."""
    kicker, title, lines = card
    k = Image.new("RGBA", (1600, 40), (0, 0, 0, 0))
    paint(k, (0, 0), kicker.upper(), font(SEMI, 24), TEAL, 5)
    t = Image.new("RGBA", (1600, 140), (0, 0, 0, 0))
    paint(t, (0, 0), title, font(BOLD, 104), TEXT)
    s = Image.new("RGBA", (1600, 48 * len(lines) + 12), (0, 0, 0, 0))
    for j, line in enumerate(lines):
        paint(s, (0, 48 * j), line, font(REG, 34), MUTED)
    layers = [(k, 180, 360, 0.0), (t, 174, 405, 0.12), (s, 180, 565, 0.35)]
    for n, (_, _, _, short) in CHAPTERS.items():
        c = Image.new("RGBA", (226, 60), (0, 0, 0, 0))
        shapes(c, lambda d: d.rounded_rectangle([0, 0, 200, 4], 2, fill=TEAL + (255,)))
        paint(c, (0, 18), f"{n:02d} {short}".upper(), font(SEMI, 18), TEXT, 2.5)
        layers.append((c, 180 + (n - 1) * 226, 950, 0.8 + 0.15 * (n - 1)))
    return layers

def rich_png(text, size, width, line_h, color=TEXT, bold_color=TEAL):
    """Text wrapped to width, with **bold** runs in bold_color, on a transparent image."""
    reg, bold = font(REG, size), font(BOLD, size)
    words, after_space = [], False  # words are (word, is bold, space before it)
    for chunk, b in runs(text):
        for j, word in enumerate(chunk.split()):
            words.append((word, b, j > 0 or chunk[0].isspace() or after_space))
        after_space = chunk[-1].isspace()
    lines, line, x = [], [], 0
    for word, b, space in words:
        f = bold if b else reg
        gap = reg.getlength(" ") if space and line else 0
        if line and x + gap + f.getlength(word) > width:
            lines.append(line)
            line, x, gap = [], 0, 0
        line.append((x + gap, word, f, bold_color if b else color))
        x += gap + f.getlength(word)
    lines.append(line)
    img = Image.new("RGBA", (width, line_h * len(lines) + 12), (0, 0, 0, 0))
    for j, line in enumerate(lines):
        for x, word, f, c in line:
            paint(img, (x, line_h * j), word, f, c)
    return img

def intro_layers():
    """The card after the title card: the use case, who it's for and the problem, then the solution."""
    k = Image.new("RGBA", (1600, 40), (0, 0, 0, 0))
    paint(k, (0, 0), INTRO["kicker"].upper(), font(SEMI, 24), TEAL, 5)
    size = next(sz for sz in range(72, 50, -2) if font(BOLD, sz).getlength(INTRO["title"]) <= 1570)
    t = Image.new("RGBA", (1600, 110), (0, 0, 0, 0))
    paint(t, (0, 0), INTRO["title"], font(BOLD, size), TEXT)
    layers = [(k, 180, 220, 0.0), (t, 174, 265, 0.12)]
    for j, (label, body) in enumerate(INTRO["columns"]):
        c = Image.new("RGBA", (760, 260), (0, 0, 0, 0))
        paint(c, (0, 0), label.upper(), font(SEMI, 20), MUTED, 3.5)
        c.alpha_composite(rich_png(body, 34, 740, 50), (0, 44))
        layers.append((c, 180 + 800 * j, 430, 0.5 + 0.4 * j))
    label, body = INTRO["solution"]
    sb = rich_png(body, 36, 1460, 52)
    h = 66 + sb.height + 22
    s = Image.new("RGBA", (1562, h + 2), (0, 0, 0, 0))
    shapes(s, lambda d: (d.rounded_rectangle([0, 0, 1560, h], 22, fill=(255, 255, 255, 16), outline=(255, 255, 255, 48), width=1),
                         d.rounded_rectangle([0, 20, 6, h - 20], 3, fill=TEAL + (255,))))
    paint(s, (40, 28), label.upper(), font(SEMI, 20), TEAL, 3.5)
    s.alpha_composite(sb, (40, 68))
    layers.append((s, 180, 700, 1.6))
    return layers

def cast_layers():
    """The cast card: who's who, a row each with its color, then the patient and the color key."""
    k = Image.new("RGBA", (1600, 40), (0, 0, 0, 0))
    paint(k, (0, 0), CAST["kicker"].upper(), font(SEMI, 24), TEAL, 5)
    t = Image.new("RGBA", (1600, 90), (0, 0, 0, 0))
    paint(t, (0, 0), CAST["title"], font(BOLD, 60), TEXT)
    layers = [(k, 180, 96, 0.0), (t, 174, 136, 0.12)]
    rh, rf, sf = 84, font(BOLD, 28), font(REG, 24)
    for j, (role, product, does, col) in enumerate(CAST["rows"]):
        r = Image.new("RGBA", (1562, rh), (0, 0, 0, 0))
        shapes(r, lambda d, col=col: (d.rounded_rectangle([0, 12, 6, rh - 14], 3, fill=col + (255,)),
                                      d.line([(0, rh - 1), (1560, rh - 1)], fill=(255, 255, 255, 28), width=1)))
        paint(r, (26, 18), role, rf, TEXT)
        for i, line in enumerate(wrap(product, sf, 520)):
            paint(r, (420, 20 + 32 * i), line, sf, MUTED)
        for i, line in enumerate(wrap(does, sf, 580)):
            paint(r, (980, 20 + 32 * i), line, sf, TEXT)
        layers.append((r, 180, 250 + rh * j, 0.4 + 0.2 * j))
    layers.append((rich_png(CAST["patient"], 32, 1560, 44), 180, 866, 2.0))
    key = Image.new("RGBA", (1560, 30), (0, 0, 0, 0))
    x, kf = 0, font(SEMI, 18)
    for label, col in CAST["legend"]:
        shapes(key, lambda d, x=x, col=col: d.rounded_rectangle([x, 11, x + 26, 17], 3, fill=col + (255,)))
        x = paint(key, (x + 38, 2), label, kf, MUTED, 1.5) + 40
    layers.append((key, 180, 952, 2.3))
    return layers

def animate(layers, dur):
    """Each layer rises in at its own time, they all hold, then fade back to the plate together."""
    bg = plate()
    for i in range(round(dur * FPS)):
        s = i / FPS
        out_p = ease((s - (dur - 0.45)) / 0.45)
        frame = bg.copy()
        for img, x, y, at in layers:
            p_in = ease((s - at) / 0.6)
            alpha = p_in * (1 - out_p)
            if alpha <= 0:
                continue
            lay = img.copy()
            lay.putalpha(lay.getchannel("A").point(lambda v, a=alpha: int(v * a)))
            frame.alpha_composite(lay, (x, y + round(36 * (1 - p_in) - 24 * out_p)))
        yield frame.convert("RGB").tobytes()

# ---------------------------------------------------------------- timing
def frames(sec): return round(sec * FPS)

def clock(item, t0=0.0):
    """A recording's parts in output time: where each starts, where each tour's pause begins (with the recording time it
    pauses at), where the recording ends, and a map from the recording's time to output time."""
    starts, tours, acc = [], [], t0
    for p in item["parts"]:
        starts.append(acc)
        if p["tour"]:
            tours.append((p["b"], acc + frames((p["b"] - p["a"]) / p["x"]) / FPS))
        acc += frames((p["b"] - p["a"]) / p["x"] + p["hold"]) / FPS
    def to_out(t):
        parts = item["parts"]
        for k, (p, s) in enumerate(zip(parts, starts)):
            if t < p["a"]:
                return s
            if t < p["b"]:
                return s + (t - p["a"]) / p["x"]
            nxt = parts[k + 1]["a"] if k + 1 < len(parts) else math.inf  # a later part's own time isn't in this hold
            if t < min(p["b"] + p["hold"], nxt) and not p["tour"]:  # a tour's pause has its own caption
                return s + (p["b"] - p["a"]) / p["x"] + (t - p["b"])
        return acc
    return starts, tours, acc, to_out

def tour_voice(tour, t):
    """The narrator's lines for a tour that starts at t: each step's, just after its box arrives."""
    lines, s = [], t + TOUR_IN
    for st in tour["steps"]:
        if st.get("say"):
            lines.append((s + VO_LEAD, st["say"]))
        s += step_s(st)
    return lines

def plan(seg, quiet=False):
    """Lay the segment out in output time: the pieces to join, then captions, badges and narration in seconds."""
    pieces, caps, badges, voice, t0 = [], [], [], [], 0.0
    for item in seg["items"]:
        if "img" in item:
            n = frames(item["dur"])
            pieces.append(dict(img=STILLS / item["img"], n=n))
            caps += [(t0 + t, text) for t, text in item["captions"]]
            voice += [(t0 + s, text) for s, text, _ in said(item.get("say", []))]
            t0 += n / FPS
            if item.get("tour"):  # then the tour on the same slide
                n = frames(tour_s(item["tour"]))
                pieces.append(dict(paused=item["tour"], img=STILLS / item["img"], n=n))
                caps.append((t0, item["tour"]["caption"]))
                badges.append((t0, t0 + n / FPS, "pause"))
                voice += tour_voice(item["tour"], t0)
                t0 += n / FPS
            continue
        acc, tour_caps = t0, []
        for p in item["parts"]:
            run_s = (p["b"] - p["a"]) / p["x"]
            p["n"] = frames(run_s + p["hold"])
            if p["x"] > 1:  # a speed badge, carried on across parts that follow each other at the same speed
                if badges and badges[-1][2] == p["x"] and abs(badges[-1][1] - acc) < 0.05:
                    badges[-1] = (badges[-1][0], acc + run_s, p["x"])
                else:
                    badges.append((acc, acc + run_s, p["x"]))
            if p["tour"]:  # play up to the pause, then the tour on the paused frame, with its own caption
                n_run = frames(run_s)
                pieces.append(dict(clip=SRC / item["clip"], **{**p, "n": n_run}))
                pieces.append(dict(paused=p["tour"], src=SRC / item["clip"], at=p["b"], crop=p["crop"], n=p["n"] - n_run))
                tour_caps.append((acc + n_run / FPS, p["tour"]["caption"]))
                badges.append((acc + n_run / FPS, acc + p["n"] / FPS, "pause"))
                voice += tour_voice(p["tour"], acc + n_run / FPS)
            else:
                pieces.append(dict(clip=SRC / item["clip"], **p))
            acc += p["n"] / FPS
        to_out = clock(item, t0)[3]
        caps += sorted([(to_out(t), text) for t, text in item["captions"]] + tour_caps)
        voice += [(s, text) for s, text, _, _ in clip_voice(item, to_out)]
        t0 = acc
    badges = [b for b in badges if b[2] == "pause" or b[1] - b[0] >= 0.8]
    timed = []
    for k, (s, text) in enumerate(caps):
        e = caps[k + 1][0] - 0.05 if k + 1 < len(caps) else t0 - FADE_S
        if e - s < 2.4 and not quiet:
            print(f"  note: short caption ({e - s:.1f} s) in {seg['key']}: {text}")
        timed.append((round(s, 3), round(e, 3), text))
    return pieces, timed, badges, sorted(voice)

# ---------------------------------------------------------------- the narration
# An AI voice narrates (O'G, 2026-11-03), and it's a Microsoft model, so the demo can say so: Grant, a MAI-Voice-2.1
# voice (public preview) in Azure Speech, from the project's Foundry resource (FOUNDRY_ACCOUNT in .env). It signs in
# as the az account with Entra ID (the resource has no keys; the account needs Cognitive Services User on it). Each
# line is kept in build/work/voice, named by a hash of its SSML, so only new or changed lines go to the service.
VOICE = "en-US-Grant:MAI-Voice-2.1"
SAY_AS = [  # written one way on screen and in the deck, said another: (pattern, what the voice says)
    (r"Microsoft 365", "Microsoft three sixty-five"), (r"gpt-5\.5", "G P T five point five"),
    (r"MAI-Voice-2\.1", "M A I Voice two point one"), (r"\bPT\b", "P.T."), (r"\bMCP\b", "M C P"),
    (r"\b6 East\b", "six East"), (r"Lindqvist", "Lindkvist")]
VO_LEAD, VO_GAP, VO_TAIL = 0.3, 0.35, 0.5  # into a pause or card before its line; between lines; after the last before a cut
RATE = 48000

def env(name):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip()
    sys.exit(f".env has no {name}")

_token = {}
def speech_auth():
    """Azure Speech's Entra ID header for the Foundry resource: Bearer aad#<resource id>#<token>."""
    if not _token or time.time() - _token["at"] > 1800:
        az = shutil.which("az") or sys.exit("The narration needs the az CLI, signed in to the demo tenant.")
        tok = subprocess.run([az, "account", "get-access-token", "--resource", "https://cognitiveservices.azure.com",
                              "--query", "accessToken", "-o", "tsv"], capture_output=True, text=True)
        if tok.returncode:
            sys.exit("az couldn't get a token for Azure Speech: " + tok.stderr.strip())
        rid = (f"/subscriptions/{env('AZURE_SUBSCRIPTION_ID')}/resourceGroups/{env('AZURE_RESOURCE_GROUP')}"
               f"/providers/Microsoft.CognitiveServices/accounts/{env('FOUNDRY_ACCOUNT')}")
        _token.update(at=time.time(), value=f"Bearer aad#{rid}#{tok.stdout.strip()}")
    return _token["value"]

def ssml(text):
    s = escape(text, quote=False)
    for pat, alias in SAY_AS:
        s = re.sub(pat, lambda m, alias=alias: f'<sub alias="{alias}">{m.group(0)}</sub>', s)
    return f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'><voice name='{VOICE}'>{s}</voice></speak>"

_voiced = {}
def voiced(text):
    """A line as speech: (wav, seconds). Synthesized once and trimmed of the silence around it."""
    if text not in _voiced:
        doc = ssml(text)
        path = WORK / "voice" / (hashlib.sha1(doc.encode()).hexdigest()[:16] + ".wav")
        if not path.exists():
            req = urllib.request.Request(f"https://{env('FOUNDRY_ACCOUNT')}.cognitiveservices.azure.com/tts/cognitiveservices/v1",
                                         data=doc.encode(), method="POST",
                                         headers={"Authorization": speech_auth(), "Content-Type": "application/ssml+xml",
                                                  "X-Microsoft-OutputFormat": "raw-48khz-16bit-mono-pcm", "User-Agent": "amc-demo-video"})
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(req, timeout=180) as r:
                        pcm = np.frombuffer(r.read(), np.int16)
                    break
                except urllib.error.HTTPError as e:
                    if e.code not in (429, 500, 502, 503) or attempt == 3:
                        sys.exit(f"Azure Speech refused a line ({e.code} {e.read()[:200]}): {text}")
                    time.sleep(5 * (attempt + 1))
            loud = np.flatnonzero(np.abs(pcm.astype(np.int32)) > 300)
            if len(loud):
                pcm = pcm[max(loud[0] - RATE // 25, 0): loud[-1] + RATE // 25]  # keep 40 ms either side
            path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(path), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(RATE)
                w.writeframes(pcm.tobytes())
        with wave.open(str(path)) as w:
            _voiced[text] = (path, w.getnframes() / RATE)
    return _voiced[text]

def said(lines):
    """Lines as [(start, text, seconds)], with a start of None put just after the line before."""
    out, end = [], 0.0
    for t, text in lines:
        d = voiced(text)[1]
        s = end + VO_GAP if t is None else t
        out.append((s, text, d))
        end = s + d
    return out

LEN = {}  # how long each card lasts, set by fit_all()

def fit_all():
    """Make room for the narration before anything is laid out: tour steps, cards, slides and held frames get as long as
    their lines need, and a sped-up stretch plays slower where a line would run into the next."""
    for key, kind, seg in order():
        if kind == "card":
            LEN[key] = CARD_S
        elif kind == "brief":  # waits for the chapter card's line to finish
            n = seg["num"]
            d = voiced(CHAPTER_SAY[n])[1] if n in CHAPTER_SAY else 0
            LEN[key] = round(max(brief_s(n), VO_LEAD + d + VO_TAIL - CARD_S), 1)
        elif kind in ("next", "intro", "cast"):
            LEN[key] = round(max([dict(next=NEXT_S, intro=INTRO_S, cast=CAST_S)[kind]] +
                                 [s + d + VO_TAIL for s, _, d in said(seg.get("say", []))]), 1)
        elif kind == "video":  # the hero's own timing is fixed, so only its last frame can wait
            lines = said(seg.get("say", []))
            for (s, text, d), nxt in zip(lines, lines[1:]):
                if s + d > nxt[0]:
                    print(f"  note: in {key}, a line runs {s + d - nxt[0]:.1f} s into the next: {text}")
            need = max([0] + [s + d + VO_TAIL for s, _, d in lines]) - (seg["end"] - seg["start"])
            seg["hold"] = round(max(seg.get("hold", 0), need), 2)
        else:
            for i, item in enumerate(seg["items"]):
                last = i == len(seg["items"]) - 1
                for tour in filter(None, [p["tour"] for p in item.get("parts", [])] + [item.get("tour")]):
                    for st in tour["steps"]:
                        if st.get("say"):
                            st["fit"] = round(max(step_s({**st, "fit": None}), VO_LEAD + voiced(st["say"])[1] + VO_GAP), 1)
                if "img" in item:
                    pad = VO_GAP if item.get("tour") or not last else VO_TAIL
                    item["dur"] = round(max([item["dur"]] + [s + d + pad for s, _, d in said(item.get("say", []))]), 1)
                else:
                    for p in item["parts"]:
                        if p["tour"]:
                            p["hold"] = tour_s(p["tour"])
                    fit_clip(key, item, VO_TAIL if last else VO_GAP)

def clip_voice(item, to_out):
    """A recording's lines in output time: (start, text, seconds, recording time or None for one that follows on)."""
    out, end = [], 0.0
    for t, text in item.get("say", []):
        d = voiced(text)[1]
        s = end + VO_GAP if t is None else to_out(t)
        out.append((s, text, d, t))
        end = s + d
    return out

def clip_room(item, pad):
    """For each line with a time of its own: (its time, the time of what comes next, seconds short). It and the lines
    that follow it on have to end before the next line with a time, the next pause, or the end (math.inf)."""
    _, tours, total, to_out = clock(item)
    lines = clip_voice(item, to_out)
    anchored = [k for k, line in enumerate(lines) if line[3] is not None]
    out = []
    for j, k in enumerate(anchored):
        t = lines[k][3]
        nxt = anchored[j + 1] if j + 1 < len(anchored) else None
        last = (nxt if nxt is not None else len(lines)) - 1  # the last line that follows this one on
        stops = [(lines[nxt][3], lines[nxt][0])] if nxt is not None else [(math.inf, total - pad)]
        stops += [(b, s + TOUR_IN) for b, s in tours if b > t]
        until, limit = min(stops, key=lambda x: x[1])
        out.append((t, until, lines[last][0] + lines[last][2] + VO_GAP - limit))
    return out

def fit_clip(key, item, pad):
    """Make room in a recording until every line fits, trying the gentlest change first: a sped-up stretch between the
    lines plays slower, then a frame there holds longer, then a part is cut in two and holds at the cut."""
    for _ in range(80):
        short = [(j, t0, t1, need) for j, (t0, t1, need) in enumerate(clip_room(item, pad)) if need > 0.02]
        if not short:
            return
        j, t0, t1, need = short[0]
        for change in room_changes(item, t0, t1, need):
            trial = copy.deepcopy(item)
            change(trial)
            if clip_room(trial, pad)[j][2] < need - 0.01:  # it helps: keep it
                change(item)
                break
        else:
            sys.exit(f"The narration doesn't fit in {key} at {t0} s: shorten a line there, or give it a later time.")
    sys.exit(f"The narration doesn't fit in {key}: shorten a line there.")

def room_changes(item, t0, t1, need):
    """Changes that might make need seconds between the recording's t0 and t1, gentlest first."""
    parts = item["parts"]
    def span(p): return min(p["b"], t1) - max(p["a"], t0)
    for k in sorted((k for k, p in enumerate(parts) if p["x"] > 1 and span(p) > 0.05),
                    key=lambda k: -span(parts[k]) * (1 - 1 / parts[k]["x"])):
        x = max(1, math.floor(span(parts[k]) / (span(parts[k]) / parts[k]["x"] + need) * 10) / 10)
        yield lambda it, k=k, x=x: it["parts"][k].update(x=x)
    for k in reversed(range(len(parts))):
        if not parts[k]["tour"] and t0 <= parts[k]["b"] <= t1:
            yield lambda it, k=k: it["parts"][k].update(hold=round(it["parts"][k]["hold"] + need, 2))
    for k, p in enumerate(parts):
        nxt = parts[k + 1]["a"] if k + 1 < len(parts) else math.inf
        if p["a"] < t1 <= p["b"] or (not p["tour"] and p["b"] < t1 < min(p["b"] + p["hold"], nxt)):
            cut = round(t1 if t1 < p["b"] else p["b"] - 0.1, 2)  # t1 is a pause or in a hold: just before the end
            if cut > max(p["a"], t0) + 0.05:
                yield lambda it, k=k, cut=cut: it["parts"].__setitem__(
                    slice(k, k + 1), [dict(it["parts"][k], b=cut, hold=need, tour=None), dict(it["parts"][k], a=cut)])

def voice_cues(timing):
    """Every narration line in the finished video's time: (start, end, text, wav), in order."""
    cues, t = [], 0.0
    for key, kind, seg in order():
        if kind == "card" and seg["num"] in CHAPTER_SAY:
            lines = said([(VO_LEAD, CHAPTER_SAY[seg["num"]])])
        elif kind in ("next", "intro", "cast", "video"):
            lines = said(seg.get("say", []))
        elif kind == "beat":
            lines = [(s, text, voiced(text)[1]) for s, text in plan(seg, quiet=True)[3]]
        else:
            lines = []
        cues += [(t + s, t + s + d, text, voiced(text)[0]) for s, text, d in lines]
        t += timing[key]["dur"]
    for (s, e, text, _), nxt in zip(cues, cues[1:]):
        if e > nxt[0] + 0.01:
            print(f"  note: narration overlaps by {e - nxt[0]:.1f} s at {s:.1f} s: {text}")
    return cues

def mix(cues, total, out):
    """The narration track: every line at its time, on silence, one 48 kHz mono WAV, speech at about -19 dBFS RMS."""
    track = np.zeros(int((total + 1) * RATE), np.int16)
    for s, _, _, path in cues:
        with wave.open(str(path)) as w:
            pcm = np.frombuffer(w.readframes(w.getnframes()), np.int16)
        i = int(round(s * RATE))
        dst = track[i:i + len(pcm)]
        track[i:i + len(pcm)] = np.clip(dst.astype(np.int32) + pcm[:len(dst)], -32768, 32767)
    speech = track[np.abs(track) > 300].astype(np.float64)
    if len(speech):
        gain = min(10 ** (-19 / 20) * 32767 / np.sqrt(np.mean(speech ** 2)), 0.89 * 32767 / np.abs(speech).max())
        for i in range(0, len(track), 10 * RATE):  # ten seconds at a time, to keep memory down
            track[i:i + 10 * RATE] = np.clip(track[i:i + 10 * RATE] * gain, -32768, 32767)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(track.tobytes())

# ---------------------------------------------------------------- ffmpeg
def run(args):
    if subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", *args]).returncode:
        sys.exit("ffmpeg failed")

ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "10", "-pix_fmt", "yuv420p", "-color_range", "tv", "-r", str(FPS)]

def build_video(seg, out):
    hold, fi, fo = seg.get("hold", 0), seg.get("fade_in", 0), seg.get("fade_out", 0)
    n = frames(seg["end"] - seg["start"] + hold)
    total = n / FPS
    WORK.mkdir(parents=True, exist_ok=True)
    plate().save(WORK / "plate.png")
    inputs = ["-ss", str(seg["start"]), "-t", str(seg["end"] - seg["start"]), "-i", str(seg["video"])]
    def looped(seconds):
        inputs.extend(["-loop", "1", "-framerate", str(FPS), "-t", f"{seconds:.3f}", "-i", str(WORK / "plate.png")])
        return inputs.count("-i") - 1
    chains = [f"[0:v]fps={FPS},tpad=stop_mode=clone:stop_duration={hold + 1},trim=end_frame={n},setpts=PTS-STARTPTS[v0]"]
    last = "v0"
    if fi:  # fade up from the plate
        chains.append(f"[{looped(fi + 0.1)}:v]format=rgba,fade=t=out:st=0:d={fi}:alpha=1[fi]")
        chains.append(f"[{last}][fi]overlay=0:0:eof_action=pass[v1]")
        last = "v1"
    if fo:  # and back to it
        chains.append(f"[{looped(fo)}:v]format=rgba,fade=t=in:st=0:d={fo}:alpha=1,setpts=PTS-STARTPTS+{total - fo:.3f}/TB[fo]")
        chains.append(f"[{last}][fo]overlay=0:0:eof_action=pass[v2]")
        last = "v2"
    chains.append(f"[{last}]format=yuv420p[out]")
    run([*inputs, "-filter_complex", ";".join(chains), "-map", "[out]", "-frames:v", str(n), "-an", *ENC, str(out)])
    return total, []

def encode(bufs, size, out):
    """Encode raw RGB frames drawn here."""
    p = subprocess.Popen([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{size[0]}x{size[1]}", "-r", str(FPS), "-i", "-", "-vf", "scale=out_range=tv,format=yuv420p", *ENC, str(out)],
                         stdin=subprocess.PIPE)
    for buf in bufs:
        p.stdin.write(buf)
    p.stdin.close()
    if p.wait():
        sys.exit(f"ffmpeg failed on {out.name}")

def build_card(layers, dur, out):
    encode(animate(layers, dur), (W, H), out)
    return dur, []

def build_beat(seg, out):
    pieces, caps, badges, _ = plan(seg)
    tmp = WORK / seg["key"]
    tmp.mkdir(parents=True, exist_ok=True)
    chrome(seg).save(tmp / "chrome.png")
    plate().save(tmp / "plate.png")
    inputs, chains = [], []
    def add_input(*args):
        inputs.extend(args)
        return inputs.count("-i") - 1
    def looped(path, seconds): return add_input("-loop", "1", "-framerate", str(FPS), "-t", f"{seconds:.3f}", "-i", str(path))
    # Each recording is one input; split it when several parts trim from it.
    uses = {}
    for k, pc in enumerate(pieces):
        if "clip" in pc:
            uses.setdefault(pc["clip"], []).append(k)
    src = {}
    for path, ks in uses.items():
        i = add_input("-i", str(path))
        if len(ks) == 1:
            src[ks[0]] = f"[{i}:v]"
        else:
            chains.append(f"[{i}:v]split={len(ks)}" + "".join(f"[s{k}]" for k in ks))
            src.update({k: f"[s{k}]" for k in ks})
    for k, pc in enumerate(pieces):
        if "img" in pc and "paused" not in pc:
            chain = f"[{looped(pc['img'], pc['n'] / FPS + 1)}:v]scale={WIN[2]}:{WIN[3]}:flags=lanczos,setsar=1,format=yuv420p"
        elif "paused" in pc:
            print(f"  drawing the tour ({pc['n'] / FPS:.1f} s)")
            draw = tour_painter(pc)
            encode((draw(i / FPS).convert("RGB").tobytes() for i in range(pc["n"])), (WIN[2], WIN[3]), tmp / f"tour{k}.mp4")
            chain = f"[{add_input('-i', str(tmp / f'tour{k}.mp4'))}:v]setsar=1,format=yuv420p"
        else:
            cx, cy, cw = pc["crop"]
            ch = round(cw * 9 / 16 / 2) * 2
            chain = (f"{src[k]}trim=start={pc['a']}:end={pc['b']},setpts=(PTS-STARTPTS)/{pc['x']},fps={FPS},"
                     f"crop={cw}:{ch}:{cx}:{cy},scale={WIN[2]}:{WIN[3]}:flags=lanczos,setsar=1,format=yuv420p")
        chains.append(f"{chain},tpad=stop_mode=clone:stop_duration=60,trim=end_frame={pc['n']},setpts=PTS-STARTPTS[p{k}]")
    n_total = sum(pc["n"] for pc in pieces)
    total = n_total / FPS
    chains.append("".join(f"[p{k}]" for k in range(len(pieces))) + f"concat=n={len(pieces)}:v=1:a=0[clip]")
    chains.append(f"color=c=0x081126:s={W}x{H}:r={FPS}:d={total:.3f}[base]")
    chains.append(f"[base][clip]overlay={WIN[0]}:{WIN[1]}:eof_action=pass[v0]")
    chains.append(f"[v0][{looped(tmp / 'chrome.png', total)}:v]overlay=0:0:eof_action=pass[v1]")
    last = "v1"
    overlays = [("cap", s, e, text) for s, e, text in caps] + [("badge", s, e, x) for s, e, x in badges]
    for k, (kind, s, e, what) in enumerate(overlays):
        png = tmp / f"{kind}{k:02d}.png"
        if kind == "cap":
            caption_png(what, png)
            xy, fin, fout = f"0:{BAND_Y}", 0.3, 0.25
        else:
            badge_png(what, png)
            xy, fin, fout = f"{WIN[0] + WIN[2] - 220 - 270}:{BAND_Y - 4}", 0.15, 0.15
        d = e - s
        chains.append(f"[{looped(png, d)}:v]format=rgba,fade=t=in:st=0:d={fin}:alpha=1,"
                      f"fade=t=out:st={d - fout:.3f}:d={fout}:alpha=1,setpts=PTS-STARTPTS+{s:.3f}/TB[o{k}]")
        chains.append(f"[{last}][o{k}]overlay={xy}:eof_action=pass[w{k}]")
        last = f"w{k}"
    if seg.get("brand"):  # rises in just after the beat fades up, then stays to the end
        bx, by = brand_png(seg["brand"], tmp / "brand.png")
        chains.append(f"[{looped(tmp / 'brand.png', total)}:v]format=rgba,fade=t=in:st=0.5:d=0.4:alpha=1[br]")
        chains.append(f"[{last}][br]overlay=x={bx}:y='{by}+16*pow(max(0,1-(t-0.5)/0.5),3)':eval=frame:eof_action=pass[wb]")
        last = "wb"
    # Fade up from the bare plate at the start and back to it at the end, so cards and beats dissolve into each other.
    chains.append(f"[{looped(tmp / 'plate.png', FADE_S + 0.1)}:v]format=rgba,fade=t=out:st=0:d={FADE_S}:alpha=1[fi]")
    chains.append(f"[{last}][fi]overlay=0:0:eof_action=pass[x1]")
    chains.append(f"[{looped(tmp / 'plate.png', FADE_S)}:v]format=rgba,fade=t=in:st=0:d={FADE_S}:alpha=1,"
                  f"setpts=PTS-STARTPTS+{total - FADE_S:.3f}/TB[fo]")
    chains.append("[x1][fo]overlay=0:0:eof_action=pass,format=yuv420p[out]")
    (tmp / "graph.txt").write_text(";\n".join(chains))
    run([*inputs, "-/filter_complex", str(tmp / "graph.txt"), "-map", "[out]", "-frames:v", str(n_total), *ENC, str(out)])
    return total, caps

# ---------------------------------------------------------------- assembly
def order():
    """(key, kind, segment) in playing order: a card goes in front of each numbered beat."""
    for seg in SEGMENTS:
        if seg.get("num"):
            yield f"card{seg['num']}", "card", seg
            yield f"brief{seg['num']}", "brief", seg
        yield seg["key"], "video" if "video" in seg else seg.get("card", "beat"), seg  # cards: next, intro, cast

def vtt_time(t): return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{t % 60:06.3f}"

# ---------------------------------------------------------------- the deck
# docs/deck.html follows the video slide for slide (O'G, 2026-11-03): a slide per segment, in the same order, and one per
# item where a beat mixes deck slides and a recording (chapter 6). A slide's data-seg names its segment ("b6.1" is b6's
# second item). The check keeps the order honest; the times (data-start, data-end) tell the recording slides which stretch
# of the video to play; the card slides are written from CHAPTERS, BRIEFS and NEXT. The notes are the deck's own.
DECK = ROOT / "docs" / "deck.html"
CARD_START, CARD_END = "<!-- card: written by scripts/build_demo_video.py -->", "<!-- /card -->"

def deck_slides():
    """(data-seg, timing key, kind, segment, item index or None) for every deck slide, in playing order."""
    for key, kind, seg in order():
        if kind == "beat" and len(seg["items"]) > 1:
            for i in range(len(seg["items"])):
                yield f"{key}.{i}", key, kind, seg, i
        else:
            yield key, key, kind, seg, None

def item_spans(seg):
    """Where each item of a beat starts and ends, in seconds from the beat's start, as plan() lays them out."""
    spans, t = [], 0.0
    for item in seg["items"]:
        if "img" in item:
            n = frames(item["dur"]) + (frames(tour_s(item["tour"])) if item.get("tour") else 0)
        else:
            n = sum(frames((p["b"] - p["a"]) / p["x"] + p["hold"]) for p in item["parts"])
        spans.append((t, t + n / FPS))
        t += n / FPS
    return spans

def deck_card(kind, seg):
    """A card slide's frame, with the same text and title size as the video's card, and its label."""
    def text(s): return escape(s, quote=False)
    def pills(names): return '<p class="v-pills">' + "".join(f"<span>{text(p)}</span>" for p in names) + "</p>"
    def lines(rows): return '<div class="v-lines">' + "".join(f"<p>{text(r)}</p>" for r in rows) + "</div>"
    def title(s, size): return f'<h1 class="v-title" style="font-size: {size / 19.2:.3f}cqw">{text(s)}</h1>'  # px to cqw at 1920
    def rich(s): return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text(s))
    def hexc(c): return "#%02x%02x%02x" % c
    if kind == "card":
        num = seg["num"]
        name, where, theme, _ = CHAPTERS[num]
        body = [f'<p class="v-num">{num:02d}</p>', f'<p class="v-kicker">{text(where)}</p>',
                title(name, 84 if font(BOLD, 84).getlength(name) < 1560 else 70), pills([theme])]
        label, lit = f"{num:02d} {name}", num
    elif kind == "brief":
        num = seg["num"]
        head, rows, pieces = BRIEFS[num]
        size = next(sz for sz in range(76, 50, -2) if font(BOLD, sz).getlength(head) <= 1570)
        body = ['<p class="v-kicker">What you\'ll see</p>', title(head, size), lines(rows), pills(pieces)]
        label, lit = f"What you'll see: {head}", num
    elif kind == "intro":
        size = next(sz for sz in range(72, 50, -2) if font(BOLD, sz).getlength(INTRO["title"]) <= 1570)
        cols = "".join(f'<div><p class="v-label">{text(label)}</p><p>{rich(body)}</p></div>' for label, body in INTRO["columns"])
        body = [f'<p class="v-kicker">{text(INTRO["kicker"])}</p>', title(INTRO["title"], size), f'<div class="v-cols">{cols}</div>',
                f'<div class="v-solution"><p class="v-label">{text(INTRO["solution"][0])}</p><p>{rich(INTRO["solution"][1])}</p></div>']
        label, lit = INTRO["title"], None
    elif kind == "cast":
        rows = "".join(f'<li style="--c: {hexc(col)}"><b>{text(role)}</b><span>{text(product)}</span><span>{text(does)}</span></li>'
                       for role, product, does, col in CAST["rows"])
        key = "".join(f'<span style="--c: {hexc(col)}">{text(name)}</span>' for name, col in CAST["legend"])
        body = [f'<p class="v-kicker">{text(CAST["kicker"])}</p>', title(CAST["title"], 60), f'<ul class="v-cast">{rows}</ul>',
                f'<p class="v-patient">{rich(CAST["patient"])}</p>', f'<p class="v-legend">{key}</p>']
        label, lit = "Meet the cast", None
    else:
        kicker, head, rows = NEXT
        body = [f'<p class="v-kicker">{text(kicker)}</p>', title(head, 104), lines(rows)]
        label, lit = head, 0
    if lit is not None:  # the chapter row: this chapter lit, or every one for the card into the details
        row = "".join(f'<li class="{"now" if n == lit or not lit else "done" if n < lit else "later"}">{n:02d} {text(c[3])}</li>'
                      for n, c in CHAPTERS.items())
        body.append(f'<ol class="v-row" aria-hidden="true">{row}</ol>')
    pad = "\n        "
    return (f'{CARD_START}\n      <div class="frame plate vcard {kind}">{pad}{pad.join(body)}\n      </div>\n      {CARD_END}',
            label)

VO_START, VO_END = "<!-- narration: written by scripts/build_demo_video.py -->", "<!-- /narration -->"

def narration_notes(part, lines):
    """A slide's notes with the narration spoken over it at the end (replacing what an earlier build wrote)."""
    part = re.sub(r"\s*" + re.escape(VO_START) + r".*?" + re.escape(VO_END), "", part, flags=re.S)
    if not lines or "</aside>" not in part:
        return part
    body = "".join(f"<p>{escape(text, quote=False)}</p>" for text in lines)
    block = f'  {VO_START}\n        <div class="narration"><p class="when">The video\'s narration</p>{body}</div>\n        {VO_END}\n      '
    k = part.rindex("</aside>")
    return part[:k] + block + part[k:]

def sync_deck(timing):
    """Check deck.html's slides against the video's order, then write their times, the card slides and the narration
    spoken over each. False if out of step."""
    slides = list(deck_slides())
    cues = voice_cues(timing)
    old = DECK.read_text(encoding="utf-8")
    head, *parts = old.split('<section class="slide')
    have = [(re.search(r'data-seg="([^"]*)"', p) or [0, "?"])[1] for p in parts]
    want = [s[0] for s in slides]
    if have != want:
        print(f"deck.html is out of step with the video. Its slides should be, in order:\n  {' '.join(want)}\nThey are:\n  {' '.join(have)}")
        return False
    starts, t = {}, 0.0
    for key, _, _ in order():
        starts[key], t = t, t + timing[key]["dur"]
    for j, (slide, key, kind, seg, i) in enumerate(slides):
        a, b = (0, timing[key]["dur"]) if i is None else item_spans(seg)[i]
        part, n = re.subn(r'data-start="[^"]*" data-end="[^"]*"', f'data-start="{starts[key] + a:.2f}" data-end="{starts[key] + b:.2f}"',
                          parts[j], count=1)
        if kind in ("card", "brief", "next", "intro", "cast"):
            card, label = deck_card(kind, seg)
            s, e = part.find(CARD_START), part.find(CARD_END)
            if min(n, s + 1, e + 1) == 0:
                print(f'deck.html: slide {slide} needs data-start="" data-end="" and the {CARD_START} {CARD_END} markers')
                return False
            part = re.sub(r'aria-label="[^"]*"', f'aria-label="{escape(label)}"', part[:s] + card + part[e + len(CARD_END):], count=1)
        elif not n:
            print(f'deck.html: slide {slide} needs data-start="" data-end=""')
            return False
        lo, hi = starts[key] + a, starts[key] + b
        parts[j] = narration_notes(part, [text for s, _, text, _ in cues if lo - 0.01 <= s < hi - 0.01])
    new = '<section class="slide'.join([head, *parts])
    if new != old:
        DECK.write_text(new, encoding="utf-8", newline="")
    print(f"deck.html: {len(slides)} slides in step with the video{' (updated)' if new != old else ''}")
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, help="segment keys to rebuild (open, intro, hero, next, cast, card1, brief1, b1, ..., end)")
    ap.add_argument("--review", action="store_true", help="contact sheets of the finished video at every caption")
    ap.add_argument("--deck", action="store_true", help="just bring deck.html into step with the last build")
    args = ap.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    timing_file = WORK / "timing.json"
    timing = json.loads(timing_file.read_text()) if timing_file.exists() else {}
    if args.review:
        return review(timing)
    fit_all()
    if args.deck:
        return sync_deck(timing) or sys.exit(1)
    for key, kind, seg in order():
        out = WORK / f"{key}.mp4"
        if key in LEN:
            want = frames(LEN[key]) / FPS
        else:
            want = frames(seg["end"] - seg["start"] + seg.get("hold", 0)) / FPS if kind == "video" else sum(pc["n"] for pc in plan(seg, quiet=True)[0]) / FPS
        stale = abs(timing.get(key, {}).get("dur", -1) - want) > 0.01  # the narration changed its length: build it again
        if args.only is not None and key not in args.only and out.exists() and not stale:
            continue
        print(f"building {key}")
        if kind == "card":
            dur, caps = build_card(card_layers(seg["num"]), LEN[key], out)
        elif kind == "brief":
            dur, caps = build_card(brief_layers(seg["num"]), LEN[key], out)
        elif kind == "next":
            dur, caps = build_card(next_layers(NEXT), LEN[key], out)
        elif kind == "intro":
            dur, caps = build_card(intro_layers(), LEN[key], out)
        elif kind == "cast":
            dur, caps = build_card(cast_layers(), LEN[key], out)
        else:
            dur, caps = build_video(seg, out) if kind == "video" else build_beat(seg, out)
        timing[key] = dict(dur=dur, caps=caps)
    timing_file.write_text(json.dumps(timing, indent=1))
    keys = [k for k, _, _ in order()]
    (WORK / "list.txt").write_text("".join(f"file '{(WORK / f'{k}.mp4').as_posix()}'\n" for k in keys))
    # Chapters (for players that list them) and captions (the narration, as spoken), both in the finished video's time.
    names = dict(open="Intro", cast="Meet the cast", end="End", **{f"card{n}": f"{n:02d} {c[0]}" for n, c in CHAPTERS.items()})
    marks, t = [], 0.0
    for k in keys:
        if k in names:
            marks.append((t, names[k]))
        t += timing[k]["dur"]
    meta = [";FFMETADATA1"]
    for j, (start, name) in enumerate(marks):
        end = marks[j + 1][0] if j + 1 < len(marks) else t
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={round(start * 1000)}", f"END={round(end * 1000)}", f"title={name}"]
    (WORK / "chapters.txt").write_text("\n".join(meta) + "\n", encoding="utf-8")
    voice = voice_cues(timing)
    OUT.with_suffix(".vtt").write_text("\n".join(["WEBVTT", ""] + [f"{vtt_time(s)} --> {vtt_time(e)}\n{text}\n" for s, e, text, _ in voice]),
                                       encoding="utf-8")
    mix(voice, t, WORK / "narration.wav")
    print(f"joining {len(keys)} segments, {t:.1f} s, {len(voice)} narration lines")
    run(["-f", "concat", "-safe", "0", "-i", str(WORK / "list.txt"), "-i", str(WORK / "chapters.txt"),
         "-i", str(WORK / "narration.wav"), "-map", "0:v", "-map", "2:a", "-map_metadata", "1", "-map_chapters", "1",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-color_range", "tv", "-r", str(FPS),
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000",  # speech at -16 LUFS, the usual level for online video
         "-c:a", "aac", "-b:a", "96k", "-ac", "1", "-shortest", "-movflags", "+faststart", str(OUT)])
    print(f"done: {OUT} ({OUT.stat().st_size / 1e6:.0f} MB, {t / 60:.1f} min)")
    if not sync_deck(timing):
        sys.exit(1)

def review(timing):
    """One frame at the middle of every caption, six to a sheet, for checking crops and captions."""
    t, times = 0.0, []
    for k, _, _ in order():
        times += [t + (s + e) / 2 for s, e, _ in timing[k]["caps"]]
        t += timing[k]["dur"]
    rev = WORK / "review"
    rev.mkdir(exist_ok=True)
    for n in range(0, len(times), 6):
        tiles = []
        for j, tt in enumerate(times[n:n + 6]):
            f = rev / f"t{n + j:03d}.jpg"
            run(["-ss", f"{tt:.2f}", "-i", str(OUT), "-frames:v", "1", "-vf", "scale=960:-2", "-q:v", "3", str(f)])
            tiles.append(Image.open(f))
        sheet = Image.new("RGB", (1920, 540 * ((len(tiles) + 1) // 2)), "black")
        for j, im in enumerate(tiles):
            sheet.paste(im, ((j % 2) * 960, (j // 2) * 540))
        sheet.save(rev / f"sheet{n // 6:02d}.jpg", quality=85)
    print(f"{len(times)} frames, sheets in {rev}")

if __name__ == "__main__":
    main()
