"""J.A.R.V.I.S. — Chainlit voice chat interface.

Run with:  chainlit run app.py -w
Click the microphone in the input bar to talk; Jarvis answers in text and
speaks the reply out loud.
"""

import io

import chainlit as cl

from jarvis.router import ask_jarvis
from jarvis.voice.stt import transcribe
from jarvis.voice.tts import synthesize

WELCOME = (
    "🤖 **J.A.R.V.I.S. online.** All systems nominal, Sir.\n\n"
    "- 🎙️ Use the microphone to talk to me — I'll speak my answers back.\n"
    "- 🌍 Ask about world news and I'll check Google live.\n"
    "- 📈 Say things like *\"research NIFTY volatility and build me a strategy\"* "
    "to run the trading pipeline (research → Pine Script → validation)."
)


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])
    cl.user_session.set("audio_buffer", None)
    await cl.Message(content=WELCOME).send()


async def _respond(user_text: str):
    history = cl.user_session.get("history")
    history.append({"role": "user", "content": user_text})

    status_msg = cl.Message(content="")

    def on_status(label: str):
        # Fire-and-forget status updates from the sync tool loop
        cl.run_sync(cl.Message(content=f"_{label}_").send())

    reply, history = await cl.make_async(ask_jarvis)(history, on_status)
    cl.user_session.set("history", history)

    elements = []
    try:
        audio = await synthesize(reply)
        if audio:
            elements.append(
                cl.Audio(name="jarvis-reply.mp3", content=audio, auto_play=True)
            )
    except Exception:
        pass  # TTS failure should never block the text reply

    status_msg.content = reply
    status_msg.elements = elements
    await status_msg.send()


@cl.on_message
async def on_message(message: cl.Message):
    await _respond(message.content)


@cl.on_audio_start
async def on_audio_start():
    cl.user_session.set("audio_buffer", io.BytesIO())
    return True


@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    buffer = cl.user_session.get("audio_buffer")
    if buffer is not None:
        buffer.write(chunk.data)


@cl.on_audio_end
async def on_audio_end():
    buffer = cl.user_session.get("audio_buffer")
    cl.user_session.set("audio_buffer", None)
    if buffer is None or buffer.getbuffer().nbytes == 0:
        return

    try:
        user_text = await cl.make_async(transcribe)(buffer.getvalue())
    except Exception as exc:
        await cl.Message(content=f"⚠️ Couldn't transcribe audio: {exc}").send()
        return

    if not user_text:
        await cl.Message(content="I didn't catch that, Sir — could you repeat?").send()
        return

    await cl.Message(content=user_text, type="user_message").send()
    await _respond(user_text)
