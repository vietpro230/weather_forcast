import os
import gradio as gr

def greet(name):
    return f"Hello, {name}!"

demo = gr.Interface(fn=greet, inputs="text", outputs="text")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Render provides the PORT
    demo.launch(server_name="0.0.0.0", server_port=port)
