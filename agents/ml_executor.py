import asyncio
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime
import torch
import transformers
from transformers import pipeline
import numpy as np
from sklearn.base import BaseEstimator
import joblib
import onnx
import onnxruntime
from prometheus_client import Counter, Histogram
import json
import aiofiles
from pathlib import Path


class MLExecutor:
    def __init__(self, model_cache_dir: str = "./cache/models"):
        self.logger = logging.getLogger("MLExecutor")
        self.model_cache_dir = Path(model_cache_dir)
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)

        # Active models
        self.loaded_models: Dict[str, Any] = {}

        # Metrics
        self.inference_counter = Counter(
            "ml_inference_total", "Total number of ML inference operations", ["model", "status"]
        )
        self.inference_duration = Histogram(
            "ml_inference_duration_seconds", "ML inference duration in seconds", ["model", "operation"]
        )

    async def load_transformers_model(self, model_name: str, task: str, device: str = "cpu") -> Dict[str, Any]:
        """Load a Hugging Face Transformers model"""
        try:
            start_time = datetime.now()

            # Create pipeline
            pipe = pipeline(task, model=model_name, device=device)

            model_key = f"{model_name}_{task}"
            self.loaded_models[model_key] = pipe

            duration = (datetime.now() - start_time).total_seconds()

            return {"model_key": model_key, "task": task, "device": device, "load_time": duration}

        except Exception as e:
            self.logger.error(f"Model loading failed: {str(e)}")
            raise

    async def run_inference(
        self, model_key: str, inputs: Union[str, List[str], Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
        """Run inference with a loaded model"""
        try:
            if model_key not in self.loaded_models:
                raise ValueError(f"Model {model_key} not loaded")

            start_time = datetime.now()

            model = self.loaded_models[model_key]
            results = model(inputs, **kwargs)

            duration = (datetime.now() - start_time).total_seconds()

            self.inference_counter.labels(model=model_key, status="success").inc()
            self.inference_duration.labels(model=model_key, operation="inference").observe(duration)

            return {"results": results, "duration": duration}

        except Exception as e:
            self.logger.error(f"Inference failed: {str(e)}")
            self.inference_counter.labels(model=model_key, status="error").inc()
            raise

    async def save_sklearn_model(self, model: BaseEstimator, model_name: str, format: str = "joblib") -> Dict[str, Any]:
        """Save a scikit-learn model"""
        try:
            start_time = datetime.now()

            path = self.model_cache_dir / f"{model_name}.{format}"

            if format == "joblib":
                joblib.dump(model, path)
            elif format == "onnx":
                # Convert to ONNX format
                from skl2onnx import convert_sklearn
                from skl2onnx.common.data_types import FloatTensorType

                initial_type = [("float_input", FloatTensorType([None, 4]))]
                onx = convert_sklearn(model, initial_types=initial_type)
                with open(path, "wb") as f:
                    f.write(onx.SerializeToString())
            else:
                raise ValueError(f"Unsupported format: {format}")

            duration = (datetime.now() - start_time).total_seconds()

            return {"path": str(path), "format": format, "save_time": duration}

        except Exception as e:
            self.logger.error(f"Model saving failed: {str(e)}")
            raise

    async def load_sklearn_model(self, model_name: str, format: str = "joblib") -> Dict[str, Any]:
        """Load a scikit-learn model"""
        try:
            start_time = datetime.now()

            path = self.model_cache_dir / f"{model_name}.{format}"

            if format == "joblib":
                model = joblib.load(path)
                self.loaded_models[model_name] = model
            elif format == "onnx":
                session = onnxruntime.InferenceSession(str(path))
                self.loaded_models[model_name] = session
            else:
                raise ValueError(f"Unsupported format: {format}")

            duration = (datetime.now() - start_time).total_seconds()

            return {"model_key": model_name, "format": format, "load_time": duration}

        except Exception as e:
            self.logger.error(f"Model loading failed: {str(e)}")
            raise

    async def run_batch_inference(
        self, model_key: str, batch_inputs: List[Union[str, Dict[str, Any]]], batch_size: int = 32, **kwargs
    ) -> Dict[str, Any]:
        """Run batch inference"""
        try:
            if model_key not in self.loaded_models:
                raise ValueError(f"Model {model_key} not loaded")

            start_time = datetime.now()
            results = []

            # Process in batches
            for i in range(0, len(batch_inputs), batch_size):
                batch = batch_inputs[i : i + batch_size]
                batch_results = await self.run_inference(model_key, batch, **kwargs)
                results.extend(batch_results["results"])

            duration = (datetime.now() - start_time).total_seconds()

            return {
                "results": results,
                "batch_count": len(batch_inputs) // batch_size + 1,
                "total_items": len(batch_inputs),
                "duration": duration,
            }

        except Exception as e:
            self.logger.error(f"Batch inference failed: {str(e)}")
            raise

    async def get_model_info(self, model_key: str) -> Dict[str, Any]:
        """Get information about a loaded model"""
        try:
            if model_key not in self.loaded_models:
                raise ValueError(f"Model {model_key} not loaded")

            model = self.loaded_models[model_key]

            info = {"model_key": model_key, "type": type(model).__name__, "device": "cpu"}  # Default

            # Get device for PyTorch models
            if hasattr(model, "device"):
                info["device"] = str(model.device)

            # Get memory usage for PyTorch models
            if isinstance(model, torch.nn.Module):
                memory_usage = (
                    sum(p.nelement() * p.element_size() for p in model.parameters()) / 1024 / 1024
                )  # Convert to MB
                info["memory_usage_mb"] = memory_usage

            return info

        except Exception as e:
            self.logger.error(f"Failed to get model info: {str(e)}")
            raise

    async def optimize_model(self, model_key: str, optimization: str = "quantization", **kwargs) -> Dict[str, Any]:
        """Optimize a loaded model"""
        try:
            if model_key not in self.loaded_models:
                raise ValueError(f"Model {model_key} not loaded")

            model = self.loaded_models[model_key]
            start_time = datetime.now()

            if optimization == "quantization":
                if isinstance(model, torch.nn.Module):
                    # Quantize PyTorch model
                    quantized_model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
                    self.loaded_models[f"{model_key}_quantized"] = quantized_model
                else:
                    raise ValueError(f"Quantization not supported for model type: {type(model)}")
            else:
                raise ValueError(f"Unsupported optimization: {optimization}")

            duration = (datetime.now() - start_time).total_seconds()

            return {
                "original_model": model_key,
                "optimized_model": f"{model_key}_quantized",
                "optimization": optimization,
                "duration": duration,
            }

        except Exception as e:
            self.logger.error(f"Model optimization failed: {str(e)}")
            raise


if __name__ == "__main__":

    async def main():
        executor = MLExecutor()

        # Load a sentiment analysis model
        model_info = await executor.load_transformers_model(
            "distilbert-base-uncased-finetuned-sst-2-english", "sentiment-analysis"
        )
        print("Model loaded:", json.dumps(model_info, indent=2))

        # Run inference
        text = "I love this product! It's amazing!"
        result = await executor.run_inference(model_info["model_key"], text)
        print("\nInference result:", json.dumps(result, indent=2))

        # Get model info
        info = await executor.get_model_info(model_info["model_key"])
        print("\nModel info:", json.dumps(info, indent=2))

    asyncio.run(main())
