"""
Test suite locking out ZeroDivisionError in EmbeddingService.encode_batch
when an empty texts list is provided.
"""

import os
import sys
from unittest.mock import MagicMock

# Mock third-party dependencies before importing embedding_service
sys.modules['FlagEmbedding'] = MagicMock()
sys.modules['colorlog'] = MagicMock()

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from embedding_service import EmbeddingService


def test_encode_batch_empty_texts_logger_zero_division():
    """
    Ensure encode_batch with an empty list of texts does not raise ZeroDivisionError
    during logging.
    """
    service = EmbeddingService.__new__(EmbeddingService)
    mock_logger = MagicMock()
    service.logger = mock_logger
    service.model = MagicMock()
    service.model.encode.return_value = {
        'dense_vecs': MagicMock(shape=(0, 768))
    }

    result = service.encode_batch([])
    assert result['num_texts'] == 0
    assert result['dimension'] == 768
