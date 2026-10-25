"""
gradcam.py - Grad-CAM for the brain tumor CNN.

Shows which regions influenced the model's prediction. It is NOT a segmentation mask and does NOT draw a tumor
boundary - always show DISCLAIMER_TEXT with it.

Fixes vs the first version: hooks are removed after every call (the old code added new hooks on every
prediction, slowing the API down over time); the input tensor is moved to the model's device (the old code
failed on GPU machines); the activation gradient uses a tensor hook (robust with in-place layers).
"""
import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

DISCLAIMER_TEXT = (
    "The highlighted region shows areas that contributed to the model's "
    "prediction. It is not a confirmed tumor boundary or medical diagnosis."
)


class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.activations = None
        self.gradients = None
        self._handle = target_layer.register_forward_hook(self._forward_hook)

    def _forward_hook(self, module, inputs, output):
        self.activations = output.detach()
        if output.requires_grad:
            output.register_hook(lambda g: setattr(self, "gradients", g.detach()))

    def remove(self):
        if self._handle is not None:
            self._handle.remove()
            self._handle = None

    def generate(self, input_tensor, class_idx=None, temperature: float = 1.0):
        with torch.enable_grad():
            self.model.zero_grad()
            output = self.model(input_tensor)
            if class_idx is None:
                class_idx = int(output.argmax(dim=1).item())
            output[:, class_idx].sum().backward()
        grads, acts = self.gradients[0], self.activations[0]          # (C, H, W)
        weights = grads.mean(dim=(1, 2))
        cam = F.relu((weights[:, None, None] * acts).sum(dim=0))
        cam = cam - cam.min()
        if cam.max() > 0:
            cam = cam / cam.max()
        probs = F.softmax(output.detach() / temperature, dim=1)[0].cpu().numpy()
        return cam.cpu().numpy(), class_idx, probs


def find_last_conv_layer(model):
    last = None
    for module in model.modules():
        if isinstance(module, torch.nn.Conv2d):
            last = module
    if last is None:
        raise ValueError("No Conv2d layer found in model.")
    return last


def preprocess_image(pil_image: Image.Image, img_size: int = 224):
    tf = transforms.Compose([
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return tf(pil_image).unsqueeze(0)


def overlay_heatmap(pil_image: Image.Image, cam: np.ndarray, img_size: int = 224, alpha: float = 0.45):
    base = np.array(pil_image.convert("RGB").resize((img_size, img_size)))
    cam_resized = cv2.resize(cam, (img_size, img_size))
    heat = cv2.cvtColor(cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET), cv2.COLOR_BGR2RGB)
    overlay = (heat * alpha + base * (1 - alpha)).astype(np.uint8)
    return Image.fromarray(heat), Image.fromarray(overlay)


def run_gradcam(model, pil_image: Image.Image, img_size: int = 224, class_idx=None, temperature: float = 1.0):
    model.eval()
    engine = GradCAM(model, find_last_conv_layer(model))
    try:
        device = next(model.parameters()).device
        x = preprocess_image(pil_image, img_size).to(device)
        x.requires_grad_(True)
        cam, pred_idx, probs = engine.generate(x, class_idx=class_idx, temperature=temperature)
    finally:
        engine.remove()
    heatmap_img, overlay_img = overlay_heatmap(pil_image, cam, img_size)
    return {"predicted_class_idx": pred_idx, "probabilities": probs, "heatmap_img": heatmap_img,
            "overlay_img": overlay_img, "disclaimer": DISCLAIMER_TEXT}
