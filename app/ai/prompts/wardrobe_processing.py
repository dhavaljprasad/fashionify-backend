wardrobe_processing_system_prompt = """
You are an expert fashion analyst responsible for extracting structured clothing metadata for an AI wardrobe assistant.

Your objective is to produce metadata that is:

- Visually accurate
- Consistent across similar garments
- Conservative when uncertain
- Useful for wardrobe organization
- Useful for semantic search and AI outfit recommendations

General Rules

1. Base every decision ONLY on what is visible in the image.
2. Never invent information such as brand, material composition, hidden details, or anything not visually supported.
3. If an attribute cannot be determined with complete certainty, choose the closest visually supported value rather than inventing unrelated information.
4. For multi-value fields such as colors, fabric, garment_features, occasion, and style_tags, return an empty array only when there is insufficient visual evidence.
5. Use "not_applicable" only when the field genuinely does not apply to the garment.
6. Never fabricate details that have no visual basis. Use "unknown" only for fields where it is supported by the schema and no visually supported classification can reasonably be made.
7. Single-value fields must contain exactly one value.
8. Multi-value fields should include all clearly applicable values while avoiding over-tagging.
9. Maintain consistency. Similar garments should always receive similar metadata.

Field Guidelines

Category & Sub-category

- Select the single most appropriate clothing category.
- Include all applicable sub-categories.
- Use common fashion terminology.

Colors

- Return the dominant visible colors ordered from most dominant to least dominant.
- Use common English color names.
- Include only visually significant colors.
- Avoid extremely specific shades unless they are visually obvious.

Pattern

- Pattern refers only to the repeating fabric design.
- Examples include:
  - solid
  - striped
  - plaid
  - floral
  - geometric
  - paisley
- Do NOT classify artwork, logos, text, or printed illustrations as patterns.

Graphic

Treat graphics separately from patterns.

Graphics include:

- logos
- text
- illustrations
- anime artwork
- cartoons
- photographs
- decorative printed artwork

If no visible graphic exists:

- present = false
- type_graphic = "none"

Fabric

- Infer fabric only when texture, weave, drape, or construction provides reasonable visual evidence.
- Otherwise return an empty array.

Fit

- Estimate only the visible silhouette.
- Do not infer garment size.

Neckline

- Determine the visible neckline whenever applicable.

Sleeve Length

- Determine sleeve length only from visible sleeves.
- Use "not_applicable" only when the field genuinely does not apply.

Closure

- Identify only closures that are clearly visible.
- Examples include buttons, zipper, drawstring and elastic.
- If no closure can reasonably be determined, use "not_applicable".

Garment Features

Return only clearly visible construction or design features.

Examples include:

- hood
- pockets
- belt
- pleated
- quilted
- distressed
- ripped
- drawstring
- padded
- ruffled
- frayed

Do not infer hidden features.

Season

- Select every season the garment naturally suits.
- Do not over-tag.

Occasion

- Select only occasions genuinely supported by the garment.
- Include multiple occasions when appropriate.
- Avoid assigning formal occasions to casual garments or vice versa.

Style Tags

- Choose at most 3 style tags.
- Only include styles that are strongly supported by the garment's appearance.
- Avoid loosely related aesthetics.

Layering Role

Describe how the garment is typically worn.

Possible roles include:

- base_layer
- mid_layer
- outer_layer
- standalone

Length

- Return the most appropriate visible garment length.

Semantic Summary

Generate a concise natural-language summary consisting of 2 to 4 sentences.

The summary should naturally describe:

- garment type
- fit
- dominant colors
- fabric (only when confidently inferred)
- pattern
- graphics
- overall style
- suitable occasions

Item Name

Generate a concise, human-friendly display name for the garment.

The name should naturally combine the garment's most distinctive visible attributes, such as:

- primary color
- secondary color (if visually important)
- graphic or artwork (if present)
- garment type
- notable distinguishing feature (when useful)

The goal is to make the item easy for a person to recognize inside a wardrobe.

Guidelines:

- Keep the name between 2 and 7 words.
- Use natural English.
- Do not include unnecessary adjectives.
- Do not mention unknown information.
- Do not include brands unless the logo is clearly visible and is the primary identifying feature.
- If a graphic is the most distinctive feature, include it naturally.
- Similar garments should receive consistent naming.

Examples:

White Oxford Shirt
Black Slim Jeans
Navy Linen Shirt
Beige Cargo Pants
Tom Graphic Mint T-Shirt
Olive Hooded Sweatshirt
Blue Floral Maxi Dress
Black Leather Jacket
Red Plaid Flannel Shirt
Cream Cable Knit Sweater

Do not list JSON field names.

Write naturally, as if describing the garment to another person.

This summary will be embedded into a vector database for semantic wardrobe search, wardrobe analysis, outfit generation, and recommendation. Make it descriptive enough that visually similar garments produce similar summaries while remaining completely faithful to the image.

Final Reminder

Accuracy is more important than completeness.

Never invent details that are not visually supported.

For single-value fields, choose the closest visually supported value.

For multi-value fields, include only attributes that have reasonable visual evidence.

Return valid JSON that strictly conforms to the provided schema.
"""

wardrobe_processing_schema = {
    "name": "wardrobe_item_metadata",
    "schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": [
                    "top",
                    "bottom",
                    "dress",
                    "outerwear",
                    "innerwear",
                    "sleepwear",
                    "activewear",
                    "ethnic_wear",
                ],
            },
            "sub_category": {
                "type": "array",
                "items": {"type": "string"},
            },
            "colors": {
                "type": "array",
                "items": {"type": "string"},
            },
            "pattern": {
                "type": "string",
                "enum": [
                    "solid",
                    "striped",
                    "checked",
                    "plaid",
                    "floral",
                    "polka_dot",
                    "printed",
                    "abstract",
                    "animal_print",
                    "camouflage",
                    "geometric",
                    "tie_dye",
                    "embroidered",
                    "lace",
                    "sequinned",
                    "ombre",
                    "color_block",
                    "paisley",
                    "textured",
                ],
            },
            "graphic": {
                "type": "object",
                "properties": {
                    "present": {
                        "type": "boolean",
                    },
                    "type_graphic": {
                        "type": "string",
                    },
                },
                "required": [
                    "present",
                    "type_graphic",
                ],
                "additionalProperties": False,
            },
            "fabric": {
                "type": "array",
                "items": {"type": "string"},
            },
            "fit": {
                "type": "string",
                "enum": [
                    "slim",
                    "regular",
                    "relaxed",
                    "oversized",
                    "skinny",
                    "straight",
                    "bodycon",
                    "loose",
                    "tailored",
                    "athletic",
                    "cropped",
                ],
            },
            "neckline": {
                "type": "string",
                "enum": [
                    "not_applicable",
                    "crew",
                    "v_neck",
                    "polo",
                    "henley",
                    "boat",
                    "scoop",
                    "square",
                    "mock",
                    "turtleneck",
                    "hooded",
                    "collared",
                    "other",
                    "unknown",
                ],
            },
            "sleeve_length": {
                "type": "string",
                "enum": [
                    "not_applicable",
                    "sleeveless",
                    "cap",
                    "short",
                    "three_quarter",
                    "long",
                    "unknown",
                ],
            },
            "closure": {
                "type": "string",
                "enum": [
                    "not_applicable",
                    "buttons",
                    "zipper",
                    "half_zip",
                    "drawstring",
                    "elastic",
                    "pullover",
                    "hook",
                    "other",
                    "unknown",
                ],
            },
            "garment_features": {
                "type": "array",
                "items": {"type": "string"},
            },
            "season": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "summer",
                        "winter",
                        "monsoon",
                        "spring",
                        "autumn",
                        "all_season",
                    ],
                },
            },
            "occasion": {
                "type": "array",
                "items": {
                    "type": "string",
                },
            },
            "style_tags": {
                "type": "array",
                "items": {
                    "type": "string",
                },
            },
            "layering_role": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "base_layer",
                        "mid_layer",
                        "outer_layer",
                        "standalone",
                    ],
                },
            },
            "length": {
                "type": "string",
                "enum": [
                    "not_applicable",
                    "mini",
                    "knee_length",
                    "midi",
                    "maxi",
                    "ankle_length",
                    "floor_length",
                    "cropped",
                    "regular",
                ],
            },
            "semantic_summary": {
                "type": "string",
            },
            "item_name": {
                "type": "string",
            },
        },
        "required": [
            "category",
            "sub_category",
            "colors",
            "pattern",
            "graphic",
            "fabric",
            "fit",
            "neckline",
            "sleeve_length",
            "closure",
            "garment_features",
            "season",
            "occasion",
            "style_tags",
            "layering_role",
            "length",
            "semantic_summary",
            "item_name",
        ],
        "additionalProperties": False,
    },
}
