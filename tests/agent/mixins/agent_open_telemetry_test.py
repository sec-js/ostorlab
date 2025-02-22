"""Unit tests for OpenTelemetryMixin module."""
import json
import sys
import tempfile
import uuid
from typing import List

import pytest

from ostorlab.agent import agent
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.message import message as agent_message
from ostorlab.agent.message import serializer
from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.testing import agent as agent_testing


class TestAgent(agent.Agent):
    """Helper class to test OpenTelemetry mixin implementation."""

    def process(self, message: agent_message.Message) -> None:
        pass


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testOpenTelemetryMixin_whenEmitMessage_shouldTraceMessage(
    agent_run_mock: agent_testing.AgentRunInstance,
) -> None:
    """Unit test for the OpenTelemetry Mixin, ensure the correct exporter has been used and trace span has been sent."""
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp_file_obj:
        agent_definition = agent_definitions.AgentDefinition(
            name="some_name", out_selectors=["v3.report.vulnerability"]
        )
        agent_settings = runtime_definitions.AgentSettings(
            key="some_key", tracing_collector_url=f"file://{tmp_file_obj.name}"
        )
        test_agent = TestAgent(
            agent_definition=agent_definition, agent_settings=agent_settings
        )

        test_agent.emit(
            "v3.report.vulnerability",
            {
                "title": "some_title",
                "technical_detail": "some_details",
                "risk_rating": "MEDIUM",
            },
        )
        test_agent.force_flush_file_exporter()

        with open(tmp_file_obj.name, "r", encoding="utf-8") as trace_file:
            trace_content = trace_file.read()
            trace_object = json.loads(trace_content)

            assert trace_object["name"] == "emit_message"
            assert trace_object["attributes"]["agent.name"] == "some_name"
            assert (
                trace_object["attributes"]["message.selector"]
                == "v3.report.vulnerability"
            )
            emitted_msg = '{"title": "some_title", "technical_detail": "some_details", "risk_rating": "MEDIUM"}'
            assert trace_object["attributes"]["message.data"] == emitted_msg
            # instrumented messages are supposed to send the message uuid, followed by trace id int and then span
            # id int.
            assert len(agent_run_mock.raw_messages[-1].key.split("-")) == 7


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testOpenTelemetryMixin_whenEmitMessage_shouldNotTruncateOriginalMessage(
    agent_run_mock: agent_testing.AgentRunInstance,
) -> None:
    """Unit test for the OpenTelemetry Mixin, ensure the correct exporter has been used and trace span has been sent."""
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp_file_obj:
        agent_definition = agent_definitions.AgentDefinition(
            name="some_name", out_selectors=["v3.report.vulnerability"]
        )
        agent_settings = runtime_definitions.AgentSettings(
            key="some_key", tracing_collector_url=f"file://{tmp_file_obj.name}"
        )
        test_agent = TestAgent(
            agent_definition=agent_definition, agent_settings=agent_settings
        )

        technical_detail = """Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum
        has been the standard dummy text ever since the 1500s, when an unknown printer took a galley of type and 
        scrambled it to make a type specimen book. when an unknown printer took a galley of type and scrambled it to 
        make a type specimen book. """
        test_agent.emit(
            "v3.report.vulnerability",
            {
                "title": "some_title",
                "technical_detail": technical_detail,
                "risk_rating": "MEDIUM",
            },
        )
        test_agent.force_flush_file_exporter()

        with open(tmp_file_obj.name, "r", encoding="utf-8") as trace_file:
            trace_content = trace_file.read()
            trace_object = json.loads(trace_content)
            assert trace_object["name"] == "emit_message"
            assert trace_object["attributes"]["agent.name"] == "some_name"
            assert (
                trace_object["attributes"]["message.selector"]
                == "v3.report.vulnerability"
            )
            assert len(trace_object["attributes"]["message.data"]) < len(
                technical_detail
            )
            assert len(agent_run_mock.raw_messages[-1].key.split("-")) == 7
        assert len(agent_run_mock.emitted_messages[0].data["technical_detail"]) == len(
            technical_detail
        )


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testOpenTelemetryMixin_whenProcessMessage_shouldTraceMessage(
    agent_mock: List[object],
) -> None:
    """Unit test for the OpenTelemtry Mixin, ensure the correct exporter has been used and trace span has been sent."""
    del agent_mock
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp_file_obj:
        agent_definition = agent_definitions.AgentDefinition(
            name="some_name", in_selectors=["v3.report.vulnerability"]
        )
        agent_settings = runtime_definitions.AgentSettings(
            key="some_key", tracing_collector_url=f"file://{tmp_file_obj.name}"
        )
        test_agent = TestAgent(
            agent_definition=agent_definition, agent_settings=agent_settings
        )
        data = {
            "title": "some_title",
            "technical_detail": "some_details",
            "risk_rating": "MEDIUM",
        }
        raw = serializer.serialize("v3.report.vulnerability", data).SerializeToString()

        message = agent_message.Message.from_data(
            "v3.control",
            {
                "control": {"agents": ["agentY", "agentX", "agentX", "agentX"]},
                "message": raw,
            },
        )

        test_agent.process_message(
            selector=f"v3.report.vulnerability.{uuid.uuid4()}", message=message.raw
        )
        test_agent.force_flush_file_exporter()

        with open(tmp_file_obj.name, "r", encoding="utf-8") as trace_file:
            trace_content = trace_file.read()
            trace_object = json.loads(trace_content)

            assert trace_object["name"] == "process_message"
            assert trace_object["attributes"]["agent.name"] == "some_name"
            assert (
                trace_object["attributes"]["message.selector"]
                == "v3.report.vulnerability"
            )
            processed_msg = '{"title": "some_title", "risk_rating": "MEDIUM", "technical_detail": "some_details"}'
            assert trace_object["attributes"]["message.data"] == processed_msg


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testOpenTelemetryMixin_whenProcessMessageWithTraceIdSpanId_shouldInjectIdInContext(
    agent_mock: List[object],
) -> None:
    """Unit test for the OpenTelemtry Mixin, ensure the correct exporter has been used and trace span has been sent."""
    del agent_mock
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp_file_obj:
        agent_definition = agent_definitions.AgentDefinition(
            name="some_name", in_selectors=["v3.report.vulnerability"]
        )
        agent_settings = runtime_definitions.AgentSettings(
            key="some_key", tracing_collector_url=f"file://{tmp_file_obj.name}"
        )
        test_agent = TestAgent(
            agent_definition=agent_definition, agent_settings=agent_settings
        )
        data = {
            "title": "some_title",
            "technical_detail": "some_details",
            "risk_rating": "MEDIUM",
        }
        raw = serializer.serialize("v3.report.vulnerability", data).SerializeToString()

        message = agent_message.Message.from_data(
            "v3.control",
            {
                "control": {"agents": ["agentY", "agentX", "agentX", "agentX"]},
                "message": raw,
            },
        )

        trace_id = 12345
        span_id = 99998

        test_agent.process_message(
            selector=f"v3.report.vulnerability.{uuid.uuid4()}-{trace_id}-{span_id}",
            message=message.raw,
        )
        test_agent.force_flush_file_exporter()

        with open(tmp_file_obj.name, "r", encoding="utf-8") as trace_file:
            trace_content = trace_file.read()
            trace_object = json.loads(trace_content)

            assert int(trace_object["context"]["trace_id"], 16) == trace_id
            assert int(trace_object["parent_id"], 16) == span_id
            assert trace_object["name"] == "process_message"
            assert trace_object["attributes"]["agent.name"] == "some_name"
            assert (
                trace_object["attributes"]["message.selector"]
                == "v3.report.vulnerability"
            )
            processed_msg = '{"title": "some_title", "risk_rating": "MEDIUM", "technical_detail": "some_details"}'
            assert trace_object["attributes"]["message.data"] == processed_msg
