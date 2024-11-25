#
# Copyright (c) 2024, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import asyncio
from datetime import datetime, timedelta
import aiohttp
import os
import sys

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.services.openai import OpenAILLMContext, OpenAILLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport

from openai.types.chat import ChatCompletionToolParam

from runner import configure

from loguru import logger

from dotenv import load_dotenv

from insert_event import insert_event

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")


async def start_insert_appointment_function(function_name, llm, context):
    # note: we can't push a frame to the LLM here. the bot
    # can interrupt itself and/or cause audio overlapping glitches.
    # possible question for Aleix and Chad about what the right way
    # to trigger speech is, now, with the new queues/async/sync refactors.
    # await llm.push_frame(TextFrame("Let me check on that."))
    logger.debug(f"Starting insert event: {function_name} ")


async def schedule_appointment(function_name, tool_call_id, args, llm, context, result_callback):
    try:
        # Extract details from the arguments
        patient_name = args.get('patient_name')
        appointment_start = args.get('appointment_start')

        if not patient_name or not appointment_start:
            raise ValueError("Patient name and appointment time are required.")

        # Parse the ISO format datetime
        appointment_datetime = datetime.fromisoformat(appointment_start)

        # Set event details
        summary = f"Appointment with Dr. SMADJA for {patient_name}"
        location = "Dr. SMADJA's Clinic"
        description = f"Medical appointment for {patient_name} with Dr. SMADJA."

        # Set end time (30 minutes after start)
        end = (appointment_datetime + timedelta(minutes=30)).isoformat()

        # Insert the event into Google Calendar
        await insert_event(summary, location, description, appointment_start, end)

        # Prepare the result
        result = {
            "success": True,
            "message": f"Appointment scheduled for {patient_name} on {appointment_datetime.strftime('%Y-%m-%d at %H:%M')}"
        }
    except Exception as e:
        result = {
            "success": False,
            "message": f"Failed to schedule appointment: {str(e)}"
        }

    await result_callback(result)


async def main():
    async with aiohttp.ClientSession() as session:
        (room_url, token) = await configure(session)

        transport = DailyTransport(
            room_url,
            token,
            "Vocca, Ton assistant médical !",
            DailyParams(
                audio_out_enabled=True,
                transcription_enabled=True,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
            ),
        )

        tts = CartesiaTTSService(
            api_key=os.getenv("CARTESIA_API_KEY"),
            voice_id=os.getenv("CARTESIA_VOICE_ID"),
        )

        llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")
        # Register a function_name of None to get all functions
        # sent to the same callback with an additional function_name parameter.
        llm.register_function(
            "insert_appointment",
            schedule_appointment,
            start_callback=start_insert_appointment_function
        )

        tools = [
            ChatCompletionToolParam(
                type="function",
                function={
                    "name": "insert_appointment",
                    "description": "insert a doctor's appointment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "patient_name": {
                                "type": "string",
                                "description": "Name of the patient."
                            },
                            "appointment_start": {
                                "type": "string",
                                "description": "Date and time of the start of the appointment in YYYY-MM-DDTHH:MM:SS "
                                               "format."},
                        },
                        "required": ["patient_name", "appointment_start"]
                    }
                },
            )
        ]
        messages = [
            {
                "role": "system",
                "content": """
                    Tu es Vocca, un assistant vocal spécialisé dans la prise de rendez-vous pour le Dr. SMADJA, médecin généraliste.
                    Tu dois:
                    1. Accueillir poliment le patient
                    2. Demander le motif de leur appel
                    3. Si c'est pour un rendez-vous:
                       - Demander le nom du patient
                       - Demander la date et l'heure souhaitées
                       - Confirmer les détails avant de programmer
                    4. Si ce n'est pas pour un rendez-vous, expliquer poliment que tu ne peux gérer que les rendez-vous
                    
                    Sois toujours professionnel, patient et bienveillant.
                    Même si le patient parle en anglais, réponds toujours en français.
                    N'utilise pas de caractères spéciaux.
                    """,
            },
        ]

        context = OpenAILLMContext(messages, tools)
        context_aggregator = llm.create_context_aggregator(context)

        pipeline = Pipeline(
            [
                transport.input(),
                context_aggregator.user(),
                llm,
                tts,
                transport.output(),
                context_aggregator.assistant(),
            ]
        )

        task = PipelineTask(
            pipeline,
            PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=True,
                report_only_initial_ttfb=True,
            ),
        )

        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            await transport.capture_participant_transcription(participant["id"])
            # Kick off the conversation.
            await task.queue_frames([context_aggregator.user().get_context_frame()])

        runner = PipelineRunner()

        await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())
