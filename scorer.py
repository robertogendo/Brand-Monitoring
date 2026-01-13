# scorer.py
from sentence_transformers import SentenceTransformer, util
import cv2
import numpy as np

MODEL = SentenceTransformer("all-MiniLM-L6-v2")


def semantic_similarity(text, brand_templates, threshold=0.65):
    emb_text = MODEL.encode(text, convert_to_tensor=True)
    emb_templates = MODEL.encode(brand_templates, convert_to_tensor=True)
    sims = util.cos_sim(emb_text, emb_templates).cpu().numpy()
    max_sim = sims.max()

    if max_sim >= threshold:
        return float(max_sim)
    else:
        return 0.0  # or None, or raise a warning

def visual_ssim(img_path1, img_path2):
    # read grayscale
    a = cv2.imread(img_path1, cv2.IMREAD_GRAYSCALE)
    b = cv2.imread(img_path2, cv2.IMREAD_GRAYSCALE)
    a = cv2.resize(a, (800, 600))
    b = cv2.resize(b, (800, 600))
    # structural similarity (simple) using normalized cross-correlation
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    norm = np.sum((a - a.mean())*(b - b.mean())) / (np.sqrt(np.sum((a-a.mean())**2)*np.sum((b-b.mean())**2))+1e-9)
    return float(norm)

