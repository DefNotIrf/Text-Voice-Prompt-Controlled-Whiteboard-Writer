import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import re
from socket_write import get_gcode_for_text, send_gcode

# Replace with your actual ESP32 IP and port
ESP32_IP = '192.168.0.1'
ESP32_PORT = 23

# Load the model and tokenizer
model_name = "HuggingFaceTB/SmolLM2-360M-Instruct"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

# Define the assistant class
class WhiteboardAssistant:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.history = [
            {
                "role": "system",
                "content": (
                    "You are Whiteboard Assistant, a voice interface for a whiteboard robot.\n"
                    "Your only functions are:\n"
                    "1. Writing text on the whiteboard.\n"
                    "2. Erasing the whiteboard.\n"
                    "3. Explaining these two functions.\n\n"
                    "⚠️ You must NEVER answer questions outside of your functions.\n"
                    "If the user asks anything unrelated (e.g., general knowledge, jokes, personal questions), reply:\n"
                    "'Sorry, I can only help with writing or erasing on the whiteboard.'\n\n"
                    "You must keep your answers short and on-topic.\n"
                    "Always redirect unrelated questions back to your whiteboard tasks.\n\n"
                    "Example interactions:\n"
                    "User: What's the weather today?\n"
                    "Assistant: Sorry, I can only help with writing or erasing on the whiteboard.\n\n"
                    "User: Please write 'Meeting at 10AM'\n"
                    "Assistant: Okay, writing 'Meeting at 10AM' on the whiteboard.\n"
                )
            }
        ]

    def generate_response(self, user_input):
        self.history.append({"role": "user", "content": user_input})
        input_text = self.tokenizer.apply_chat_template(
            self.history,
            tokenize=False,
            add_generation_prompt=True
        )
        inputs = self.tokenizer(input_text, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
        self.history.append({"role": "assistant", "content": response})
        return response
    
# List of question words to check
QUESTION_WORDS = ["what", "how", "why", "when", "where", "who", "whom", "which", "whose", "is", "are", "do", "does", "can", "could", "would", "should"]

def is_question(user_input):
    """Check if the input is a question based on common question words."""
    return any(user_input.lower().strip().startswith(word) for word in QUESTION_WORDS)

def send_to_whiteboard(text):
    """Convert text to G-code and send it to the whiteboard robot via socket."""
    print(f"[Whiteboard] Writing: {text}")
    gcode_commands = get_gcode_for_text(text)
    send_gcode(ESP32_IP, ESP32_PORT, gcode_commands)

def erase_whiteboard():
    # Placeholder for future erasing functionality
    print("[Whiteboard] Erasing content...")

# Main loop to interact with the assistant
def main():
    assistant = WhiteboardAssistant(model, tokenizer)
    print("Assistant: How can I help you today?")
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # Skip robot commands if this is a question
        if not is_question(user_input):

            # Flexible write command detection
            write_match = re.search(
                r"(?:write(?:\s*this)?|can you write|please write|i want you to write)[:\s]*['\"]?(.*?)['\"]?$",
                user_input.strip(),
                re.IGNORECASE
            )
            if write_match:
                text_to_write = write_match.group(1).strip()
                send_to_whiteboard(text_to_write)
                continue

            # Erase command detection
            if re.search(r"\b(erase|clear)\b", user_input.lower()):
                erase_whiteboard()
                continue

        # Otherwise let the model respond
        response = assistant.generate_response(user_input)
        print(f"Assistant: {response}")

if __name__ == "__main__":
    main()