import pytest
import asyncio
import torch
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch
from transformers import pipeline
from sklearn.ensemble import RandomForestClassifier
from jarvis_assistant.agents.ml_executor import MLExecutor

@pytest.fixture
def temp_model_dir(tmp_path):
    """Create a temporary directory for model storage"""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    return model_dir

@pytest.fixture
async def ml_executor(temp_model_dir):
    """Create an ML executor instance for testing"""
    executor = MLExecutor(model_cache_dir=str(temp_model_dir))
    yield executor

@pytest.mark.asyncio
async def test_load_transformers_model(ml_executor):
    """Test loading a Hugging Face Transformers model"""
    model_info = await ml_executor.load_transformers_model(
        'distilbert-base-uncased-finetuned-sst-2-english',
        'sentiment-analysis'
    )
    assert model_info['model_key'] is not None
    assert model_info['task'] == 'sentiment-analysis'
    assert model_info['load_time'] > 0

@pytest.mark.asyncio
async def test_run_inference(ml_executor):
    """Test running inference with a loaded model"""
    # Load model first
    model_info = await ml_executor.load_transformers_model(
        'distilbert-base-uncased-finetuned-sst-2-english',
        'sentiment-analysis'
    )
    
    # Run inference
    text = "I love this product! It's amazing!"
    result = await ml_executor.run_inference(
        model_info['model_key'],
        text
    )
    
    assert result['results'] is not None
    assert result['duration'] > 0

@pytest.mark.asyncio
async def test_save_sklearn_model(ml_executor, temp_model_dir):
    """Test saving a scikit-learn model"""
    # Create a simple model
    model = RandomForestClassifier(n_estimators=10)
    X = np.random.rand(100, 4)
    y = np.random.randint(0, 2, 100)
    model.fit(X, y)
    
    # Save model
    save_info = await ml_executor.save_sklearn_model(
        model,
        'test_rf_model',
        format='joblib'
    )
    
    assert Path(save_info['path']).exists()
    assert save_info['format'] == 'joblib'
    assert save_info['save_time'] > 0

@pytest.mark.asyncio
async def test_load_sklearn_model(ml_executor, temp_model_dir):
    """Test loading a scikit-learn model"""
    # First save a model
    model = RandomForestClassifier(n_estimators=10)
    X = np.random.rand(100, 4)
    y = np.random.randint(0, 2, 100)
    model.fit(X, y)
    
    await ml_executor.save_sklearn_model(
        model,
        'test_rf_model',
        format='joblib'
    )
    
    # Load model
    load_info = await ml_executor.load_sklearn_model(
        'test_rf_model',
        format='joblib'
    )
    
    assert load_info['model_key'] == 'test_rf_model'
    assert load_info['format'] == 'joblib'
    assert load_info['load_time'] > 0

@pytest.mark.asyncio
async def test_batch_inference(ml_executor):
    """Test batch inference"""
    # Load model first
    model_info = await ml_executor.load_transformers_model(
        'distilbert-base-uncased-finetuned-sst-2-english',
        'sentiment-analysis'
    )
    
    # Run batch inference
    texts = [
        "I love this product!",
        "This is terrible.",
        "Not bad, could be better."
    ]
    
    result = await ml_executor.run_batch_inference(
        model_info['model_key'],
        texts,
        batch_size=2
    )
    
    assert len(result['results']) == len(texts)
    assert result['batch_count'] == 2
    assert result['duration'] > 0

@pytest.mark.asyncio
async def test_model_optimization(ml_executor):
    """Test model optimization"""
    # Create a simple PyTorch model
    class SimpleModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(10, 2)
            
        def forward(self, x):
            return self.linear(x)
    
    model = SimpleModel()
    model_key = "test_simple_model"
    ml_executor.loaded_models[model_key] = model
    
    # Optimize model
    opt_info = await ml_executor.optimize_model(
        model_key,
        optimization='quantization'
    )
    
    assert opt_info['original_model'] == model_key
    assert opt_info['optimized_model'] == f"{model_key}_quantized"
    assert opt_info['optimization'] == 'quantization'
    assert opt_info['duration'] > 0

@pytest.mark.asyncio
async def test_get_model_info(ml_executor):
    """Test getting model information"""
    # Load a model first
    model_info = await ml_executor.load_transformers_model(
        'distilbert-base-uncased-finetuned-sst-2-english',
        'sentiment-analysis'
    )
    
    # Get model info
    info = await ml_executor.get_model_info(model_info['model_key'])
    
    assert info['model_key'] == model_info['model_key']
    assert 'type' in info
    assert 'device' in info

@pytest.mark.asyncio
async def test_error_handling(ml_executor):
    """Test error handling"""
    with pytest.raises(ValueError):
        await ml_executor.get_model_info('nonexistent_model')
    
    with pytest.raises(ValueError):
        await ml_executor.run_inference('nonexistent_model', "test")
