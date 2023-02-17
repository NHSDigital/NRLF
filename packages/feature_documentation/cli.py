from feature_documentation import generate, push
from fire import Fire

if __name__ == "__main__":
    Fire({"generate": generate, "push": push})
