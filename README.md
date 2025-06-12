# Text-Voice-Prompt-Controlled-Whiteboard-Writer
This project enables controlling a whiteboard writing application using voice commands and integrates camera and cloud modules.

Project Structure
- `whiteboard.py`  
  The overall system which integrates all the functions.
- `write_module.py`  
  Handles the writing functions.
- `erase_module.py`  
  Manages the erasing functions.
- `gcode_data.py`  
  Contains all the G-code commands used for the writing module.
- `config.json`
  Saves all the calibration values for the writing and erasing head.
- `requirements.txt`  
  Lists all Python dependencies required for the project.

Getting Started
1. Clone the repository:
   ```bash
   git clone https://github.com/DefNotIrf/Text-Voice-Prompt-Controlled-Whiteboard-Writer.git
   cd Text-Voice-Prompt-Controlled-Whiteboard-Writer
