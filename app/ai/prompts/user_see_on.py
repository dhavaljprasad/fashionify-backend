user_see_on_prompt = """
You are given two reference images:

1. reference_0.webp — the person.
2. reference_1.webp — the garment.

Generate a photorealistic virtual try-on image of the person in reference_0.webp wearing the exact garment from reference_1.webp.

Requirements:
- Preserve the person in reference_0.webp's identity exactly: face, skin tone, hairstyle, body shape, and proportions.
- Preserve the person in reference_0.webp's original pose, camera angle, framing, and background as closely as possible. Do not change the pose unless absolutely necessary to fit the garment naturally.
- Preserve the natural lighting and overall look of the reference_0.webp photo. Do not retouch the skin, smooth the face, enhance makeup, sharpen features, or create a studio-quality or glamour effect.
- Use the exact garment from reference_1.webp, preserving its color, pattern, texture, silhouette, neckline, sleeves, hem, and all design details.
- Fit the garment realistically to the person in reference_0.webp's shoulders, chest, waist, hips, arms, and legs.
- If the garment appears tight, show natural stretching and fabric tension.
- If the garment appears loose, show realistic folds and draping.
- Do not redesign, beautify, or reinterpret the garment.

Goal:
Produce a realistic "as-if photographed" image where the same person, in the same pose and environment, is naturally wearing the exact garment with accurate fit and authentic fabric behavior.
"""
