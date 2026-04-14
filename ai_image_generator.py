import replicate

def generate_image(prompt):
    output = replicate.run(
        "stability-ai/sdxl:latest",
        input={
            "prompt": prompt,
            "width": 1024,
            "height": 1792
        }
    )

    return output[0]
