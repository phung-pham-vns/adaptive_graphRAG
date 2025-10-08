import asyncio
import requests
import logging
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Pipe:
    class Valves(BaseModel):
        """Configuration settings."""

        API_BASE_URL: str = Field(
            default="http://host.docker.internal:8000",
            description="Adaptive RAG API endpoint URL",
        )

        SHOW_WORKFLOW_STEPS: bool = Field(
            default=True, description="Show detailed workflow steps in real-time"
        )

        SHOW_CITATIONS: bool = Field(
            default=True, description="Show sources and citations"
        )

        SHOW_METADATA: bool = Field(
            default=True, description="Show metadata (route, timing, steps count)"
        )

        TIMEOUT_SECONDS: int = Field(
            default=120, description="Request timeout in seconds"
        )

    def __init__(self):
        self.type = "manifold"
        self.id = "plant_doctor_v1"
        self.name = "PlantDoctorV1"
        self.valves = self.Valves()

    def pipes(self) -> list[dict[str, str]]:
        return [
            {"id": "naive_graph_rag", "name": "Naive Graph RAG"},
        ]

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> str:
        """
        Main pipe function that processes messages through Adaptive RAG workflow.

        :param body: Request body with messages
        :param __user__: User information
        :param __event_emitter__: Event emitter for status updates
        :return: Generated answer with citations and workflow information
        """
        
        # Log execution start
        request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        logger.info(f"[{request_id}] ========== PIPELINE EXECUTION START ==========")
        logger.info(f"[{request_id}] User: {__user__.get('name', 'Unknown') if __user__ else 'Unknown'}")

        # Extract question and image from messages
        messages = body.get("messages", [])
        if not messages:
            return "❌ No messages provided."

        # Get last user message
        question = ""
        image_data = None
        
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                
                # Handle different content formats
                if isinstance(content, str):
                    question = content
                elif isinstance(content, list):
                    # Handle multimodal content (text + images)
                    for item in content:
                        if item.get("type") == "text":
                            question = item.get("text", "")
                        elif item.get("type") == "image_url":
                            image_url = item.get("image_url", {}).get("url", "")
                            if image_url.startswith("data:"):
                                # Extract base64 data from data URL
                                image_data = image_url
                            else:
                                logger.warning(f"[{request_id}] Non-data URL image detected: {image_url[:50]}...")
                break

        if not question:
            logger.warning(f"[{request_id}] No question found in messages")
            return "❌ No question found in messages."

        # Log input details
        if image_data:
            logger.info(f"[{request_id}] Question: {question[:100]}... (with image)")
        else:
            logger.info(f"[{request_id}] Question: {question[:100]}...")
        
        # Get selected model
        model_id = body.get("model", "naive_graph_rag")
        logger.info(f"[{request_id}] Model: {model_id}")

        # Determine mode from model
        if "naive_graph_rag" in model_id:
            mode = "naive_graph_rag"
            mode_display = "GraphRAG"

        # Emit initial status
        if __event_emitter__:
            input_type = "multimodal (text + image)" if image_data else "text-only"
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"🚀 Starting workflow ({mode_display} mode, {input_type})...",
                        "done": False,
                    },
                }
            )
            await asyncio.sleep(0.1)

        try:
            # Get configuration
            request_body = self.get_request_body(mode)

            # Build request payload
            payload = {
                "question": question,
                **request_body,
            }
            
            # Add image if present
            if image_data:
                payload["image"] = image_data

            # Call API
            logger.info(f"[{request_id}] Calling API: {self.valves.API_BASE_URL}/workflow/run")
            response = requests.post(
                f"{self.valves.API_BASE_URL}/workflow/run",
                json=payload,
                timeout=self.valves.TIMEOUT_SECONDS,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"[{request_id}] API call successful")

            # Check success
            if not data.get("success", False):
                error = data.get("answer", "Unknown error")
                return f"❌ Error: {error}"

            if __event_emitter__ and self.valves.SHOW_WORKFLOW_STEPS:
                workflow_steps = data.get("workflow_steps", [])
                for step_index, step_info in enumerate(workflow_steps):
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": f"✅ Step {step_index + 1}/{len(workflow_steps)}: Run {step_info['name']} - Time: {step_info['processing_time']}s",
                                "done": False,
                            },
                        }
                    )
                    await asyncio.sleep(0.05)

            # Emit completion
            metadata = data.get("metadata", {})
            total_time = metadata.get("total_processing_time", 0)
            total_steps = metadata.get("total_steps", 0)

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"✅ Workflow completed! ({total_steps} steps in {total_time:.1f}s)",
                            "done": True,
                        },
                    }
                )

            logger.info(f"[{request_id}] ========== PIPELINE EXECUTION END ==========")
            return self.format_response(data, image_processed=bool(image_data))

        except requests.exceptions.Timeout:
            logger.error(f"[{request_id}] Request timeout")
            return (
                f"⏱️ **Request timed out** after {self.valves.TIMEOUT_SECONDS}s\n\n"
                "**Suggestions:**\n"
                "1. Increase TIMEOUT_SECONDS in settings\n"
                "2. Try using Speed mode\n"
                "3. Check if API is responding slowly"
            )

        except requests.exceptions.ConnectionError:
            logger.error(f"[{request_id}] Connection error to {self.valves.API_BASE_URL}")
            return (
                f"🔌 **Cannot connect to API** at `{self.valves.API_BASE_URL}`\n\n"
                "**Troubleshooting steps:**\n"
                "1. Verify API is running:\n"
                "   ```bash\n"
                "   curl http://localhost:8000/health\n"
                "   ```\n"
                "2. Check API_BASE_URL in pipe settings\n"
                "3. Verify Docker networking:\n"
                "   ```bash\n"
                "   docker exec openwebui-adaptive-rag curl http://host.docker.internal:8000/health\n"
                "   ```\n"
            )

        except requests.exceptions.HTTPError as e:
            logger.error(f"[{request_id}] HTTP error: {e.response.status_code}")
            return (
                f"❌ **API Error** {e.response.status_code}\n\n"
                f"```\n{e.response.text[:500]}\n```"
            )

        except Exception as e:
            logger.error(f"[{request_id}] Unexpected error: {str(e)}")
            return f"❌ **Unexpected error:** {str(e)}"

    def get_request_body(self, mode: str) -> dict:
        configs = {
            "naive_graph_rag": {
                "n_retrieved_documents": 10,
                "n_web_searches": 10,
                "node_retrieval": True,
                "edge_retrieval": True,
                "episode_retrieval": False,
                "community_retrieval": False,
                "enable_retrieved_documents_grading": False,
                "enable_hallucination_checking": False,
                "enable_answer_quality_checking": False,
            },
        }
        return configs.get(mode.lower(), configs["naive_graph_rag"])

    def format_response(self, response: dict[str, any], image_processed: bool = False) -> str:
        parts = []

        # Main answer
        answer = response.get("answer", "No answer generated.")
        parts.append(answer)

        # Add separator before metadata
        parts.append("\n\n---")
        
        # Add input type indicator
        if image_processed:
            parts.append("\n### 📸 Input Type")
            parts.append("**Multimodal Analysis** (Text + Image)")
            parts.append("")

        # Citations
        if self.valves.SHOW_CITATIONS:
            citations = response.get("citations", [])
            if citations:
                kg_cites = [c for c in citations if not c.get("url")]
                web_cites = [c for c in citations if c.get("url")]

                if kg_cites or web_cites:
                    parts.append("\n### 📚 Sources")

                if kg_cites:
                    parts.append("\n**Knowledge Graph:**")
                    for i, c in enumerate(kg_cites[:5], 1):
                        title = c.get("title", "Unknown")
                        parts.append(f"{i}. {title}")

                if web_cites:
                    parts.append("\n**Web:**")
                    for i, c in enumerate(web_cites[:5], 1):
                        title = c.get("title", "Unknown")
                        url = c.get("url", "")
                        parts.append(f"{i}. [{title}]({url})")

        return "\n".join(parts)
