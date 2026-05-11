import time
import torch
from transformers import AutoModelForCausalLM, AutoModelForVision2Seq, AutoProcessor
from transformers.generation import TextIteratorStreamer

class VLMBackend:
    def __init__(self, config, model_id):
        self.model_config = config
        self.model_id = model_id
        self.model_type = config.model_type
        self.model = None
        self.image_encoding_time = 0
        self.t0 = 0
        self.processor = None
        self.model_loading_time = 0

    def load_model(self):
        raise NotImplementedError("Subclasses must implement load_model()")
    
    def run(self, image, prompt):
        raise NotImplementedError("Subclasses must implement run()")
    
class BackendFactory:
    def __new__(cls, model_id: str, config):
        if "moondream2" in model_id.lower():
            return Moondream2Backend(config=config, model_id=model_id)
        else:
            try:
                return DefaultBackend(config=config, model_id=model_id)
            except Exception as e:
                raise ValueError(f"Error: {e}")

                
class Moondream2Backend(VLMBackend):
    def __init__(self, config, model_id):
        super().__init__(config, model_id)
        self.load_model()

    def load_model(self):
        loading_start = time.time()

        self.model = AutoModelForCausalLM.from_pretrained(self.model_id, trust_remote_code=True)
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[INFO] Using device: {device}")
        self.model = self.model.to(device)
        self.model.eval()

        loading_end = time.time()
        self.model_loading_time = loading_end - loading_start
        print(f"Model loading time: {loading_end - loading_start:.2f} seconds")
    
    def run(self, image, prompt):
        image_encoding_start = time.time()
        enc_image = self.model.encode_image(image)
        self.image_encoding_time = time.time() - image_encoding_start

        self.t0 = time.time()
        return self.model.query(
            enc_image,
            prompt,
            stream=True
        )["answer"]
    
class DefaultBackend(VLMBackend):
    def __init__(self, config, model_id):
        super().__init__(config, model_id)
        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        self.load_model()

    def load_model(self):
        loading_start = time.time()

        self.model = AutoModelForVision2Seq.from_pretrained(self.model_id,
                                                            trust_remote_code=True,
                                                            device_map="auto",         # Optimizes device placement
                                                            low_cpu_mem_usage=True,    # Skips redundant weight initialization
                                                            torch_dtype="auto",        # Loads in the best precision (e.g., fp16)
                                                            use_safetensors=True)      # Uses faster, memory-mapped file format
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[INFO] Using device: {device}")
        self.model = self.model.to(device)  # Move model once at init

        loading_end = time.time()
        self.model_loading_time = loading_end - loading_start
        print(f"Model loading time: {loading_end - loading_start:.2f} seconds")
    
    def run(self, image, prompt):
        image_encoding_start = time.time()
        # Build the multimodal input
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(
            images=image.convert("RGB"), 
            text=text,
            return_tensors="pt"
        )
        self.image_encoding_time = time.time() - image_encoding_start

        inputs = inputs.to(self.model.device)

        streamer = TextIteratorStreamer(
            self.processor.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )
        
        self.t0 = time.time()
        out_stream = self.model.generate(
            **inputs, 
            streamer=streamer,
            max_new_tokens=500)

        return streamer

    
