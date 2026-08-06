"""
Test script for multimodal agent functionality
"""

import asyncio
import unittest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from agent import MultimodalAgent, MultimodalContent, MultimodalTools, Message
from config import ExtractionMode, Provider


class TestMultimodalContent(unittest.TestCase):
    """Test MultimodalContent class"""
    
    def test_content_creation(self):
        """Test creating multimodal content"""
        content = MultimodalContent(
            type="image",
            path="test.jpg",
            mime_type="image/jpeg"
        )
        
        self.assertEqual(content.type, "image")
        self.assertEqual(content.path, "test.jpg")
        self.assertEqual(content.mime_type, "image/jpeg")
        
    def test_get_base64(self):
        """Test base64 encoding"""
        content = MultimodalContent(
            type="text",
            data=b"Hello World"
        )
        
        base64_str = content.get_base64()
        self.assertEqual(base64_str, "SGVsbG8gV29ybGQ=")


class TestMessage(unittest.TestCase):
    """Test Message class"""
    
    def test_message_creation(self):
        """Test creating messages"""
        msg = Message(
            role="user",
            content="Hello"
        )
        
        self.assertEqual(msg.role, "user")
        self.assertEqual(msg.content, "Hello")
        
    def test_message_to_dict(self):
        """Test converting message to dictionary"""
        msg = Message(
            role="assistant",
            content="Hi there",
            tool_calls=[{"id": "1", "function": {"name": "test"}}]
        )
        
        msg_dict = msg.to_dict()
        self.assertEqual(msg_dict["role"], "assistant")
        self.assertEqual(msg_dict["content"], "Hi there")
        self.assertIn("tool_calls", msg_dict)


class TestMultimodalAgent(unittest.IsolatedAsyncioTestCase):
    """Test MultimodalAgent class"""
    
    async def test_agent_initialization(self):
        """Test agent initialization"""
        agent = MultimodalAgent(
            model="gemini-3.5-flash",
            mode=ExtractionMode.NATIVE,
            enable_tools=False
        )
        
        self.assertEqual(agent.current_model, "gemini-3.5-flash")
        self.assertEqual(agent.extraction_mode, ExtractionMode.NATIVE)
        self.assertFalse(agent.enable_multimodal_tools)
        self.assertIsNone(agent.tools)
        
    async def test_agent_with_tools(self):
        """Test agent initialization with tools"""
        agent = MultimodalAgent(
            model="gemini-3.5-flash",
            mode=ExtractionMode.EXTRACT_TO_TEXT,
            enable_tools=True
        )
        
        self.assertTrue(agent.enable_multimodal_tools)
        self.assertIsNotNone(agent.tools)
        self.assertEqual(len(agent.tool_definitions), 3)
        
    async def test_conversation_history(self):
        """Test conversation history management"""
        agent = MultimodalAgent()
        
        # Add messages
        agent.add_message(Message(role="user", content="Hello"))
        agent.add_message(Message(role="assistant", content="Hi"))
        
        history = agent.get_conversation_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")
        
        # Reset conversation
        agent.reset_conversation()
        history = agent.get_conversation_history()
        self.assertEqual(len(history), 0)
        
    @patch('agent.genai.Client')
    async def test_extract_pdf_to_text(self, mock_client_class):
        """Test PDF extraction to text"""
        agent = MultimodalAgent(mode=ExtractionMode.EXTRACT_TO_TEXT)
        
        # Mock Gemini response
        mock_response = Mock()
        mock_response.candidates = []
        mock_response.text = "Extracted PDF text"
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        content = MultimodalContent(
            type="pdf",
            data=b"PDF content"
        )
        
        result = await agent._extract_pdf_to_text(content)
        self.assertEqual(result, "Extracted PDF text")
        
    @patch('agent.AsyncOpenAI')
    async def test_extract_image_to_text(self, mock_openai_class):
        """Test image extraction to text"""
        agent = MultimodalAgent(mode=ExtractionMode.EXTRACT_TO_TEXT)
        
        # Mock OpenAI response
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Image description"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        content = MultimodalContent(
            type="image",
            data=b"Image data",
            mime_type="image/jpeg"
        )
        
        result = await agent._extract_image_to_text(content)
        self.assertEqual(result, "Image description")
        
    @patch('agent.genai.Client')
    async def test_process_native_gemini(self, mock_client_class):
        """Test native Gemini processing"""
        agent = MultimodalAgent(
            model="gemini-3.5-flash",
            mode=ExtractionMode.NATIVE
        )
        
        # Mock Gemini response
        mock_response = Mock()
        mock_response.candidates = []
        mock_response.text = "Gemini analysis result"
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        content = MultimodalContent(
            type="pdf",
            data=b"PDF content"
        )
        
        result = await agent._process_native_gemini(content, "Analyze this")
        self.assertEqual(result, "Gemini analysis result")


class TestMultimodalTools(unittest.IsolatedAsyncioTestCase):
    """Test MultimodalTools class"""
    
    async def test_tools_initialization(self):
        """Test tools initialization"""
        agent = MultimodalAgent(enable_tools=True)
        tools = MultimodalTools(agent)
        
        self.assertEqual(tools.agent, agent)
        
    @patch('agent.AsyncOpenAI')
    async def test_analyze_image_tool(self, mock_openai_class):
        """Test image analysis tool"""
        agent = MultimodalAgent(enable_tools=True)
        
        # Mock OpenAI response
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Image analysis"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Create temporary test image
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b"test image data")
            tmp_path = tmp.name
            
        try:
            result = await agent.tools.analyze_image(tmp_path, "What's in this image?")
            self.assertEqual(result, "Image analysis")
        finally:
            Path(tmp_path).unlink()


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
