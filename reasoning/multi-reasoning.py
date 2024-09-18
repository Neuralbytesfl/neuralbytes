import ollama
import time
import sys
import textwrap

# Define the model to be used consistently across all functions
MODEL_NAME = "ajindal/llama3.1-storm:8b"

def get_response(prompt):
    """
    Fetches the initial comprehensive response from the AI model based on the user prompt.
    """
    message = {"role": "user", "content": prompt}

    # Display progress
    print("\nGenerating initial response...", end=' ', flush=True)

    try:
        # Get the response from the Ollama chat model with streaming
        response_stream = ollama.chat(
            model=MODEL_NAME,
            messages=[message],
            stream=True,
        )

        # Accumulate the response
        ai_response = ""
        for chunk in response_stream:
            content = chunk.get("message", {}).get("content", "")
            ai_response += content

        print("Done.\n")  # Indicate completion

        return ai_response.strip()
    except Exception as e:
        print(f"\nAn error occurred during initial response generation: {e}\n")
        return ""

def think(prompt):
    """
    AI thinks deeply about the prompt and provides a detailed reflection.
    """
    system_message = (
        "You are an expert analyst and coder. "
        "Provide a detailed reflection on the following topic, maintaining context from previous steps. "
        "Format your response using numbered steps with titles and subheaders where applicable. "
        "Include Python code blocks using triple backticks if needed.\n\n"
        
        f"{prompt}"
    )
    message = {"role": "system", "content": system_message}

    # Display progress
    print("Thinking...", end=' ', flush=True)

    try:
        thinking_stream = ollama.chat(
            model=MODEL_NAME,
            messages=[message],
            stream=True,
        )

        thinking_response = ""
        for chunk in thinking_stream:
            content = chunk.get("message", {}).get("content", "")
            thinking_response += content

        print("Done.\n")

        return thinking_response.strip()
    except Exception as e:
        print(f"\nAn error occurred during thinking step: {e}\n")
        return ""

def process(thinking_response):
    """
    Processes the AI's reflection and summarizes key points.
    """
    system_message = (
        "You are an expert in summarizing and structuring information. "
        "Summarize the following detailed reflection into key actionable steps, maintaining context from previous steps. "
        "Ensure that each step is numbered and includes a title and subheaders if applicable. "
        "Maintain any code blocks with proper formatting.\n\n"
        f"{thinking_response}"
    )
    message = {"role": "system", "content": system_message}

    # Display progress
    print("Processing...", end=' ', flush=True)

    try:
        processing_stream = ollama.chat(
            model=MODEL_NAME,
            messages=[message],
            stream=True,
        )

        processing_response = ""
        for chunk in processing_stream:
            content = chunk.get("message", {}).get("content", "")
            processing_response += content

        print("Done.\n")

        return processing_response.strip()
    except Exception as e:
        print(f"\nAn error occurred during processing step: {e}\n")
        return ""

def analyze(processing_response):
    """
    Analyzes the summarized steps to extract actionable insights and evaluations.
    """
    system_message = (
        "You are an expert analyst and coder. "
        "Analyze the following summarized steps to extract actionable insights, identify key challenges, and provide comprehensive evaluations, maintaining context from previous steps. "
        "Format your response using numbered steps with titles and subheaders where applicable. "
        "Ensure that any included Python code blocks are properly formatted using triple backticks.\n\n"
        f"{processing_response}"
    )
    message = {"role": "system", "content": system_message}

    # Display progress
    print("Analyzing...", end=' ', flush=True)

    try:
        analyzing_stream = ollama.chat(
            model=MODEL_NAME,
            messages=[message],
            stream=True,
        )

        analyzing_response = ""
        for chunk in analyzing_stream:
            content = chunk.get("message", {}).get("content", "")
            analyzing_response += content

        print("Done.\n")

        return analyzing_response.strip()
    except Exception as e:
        print(f"\nAn error occurred during analyzing step: {e}\n")
        return ""

def format_final_output(text):
    """
    Formats the final analysis result using Markdown-like syntax and text wrapping.
    Ensures that any code blocks are properly enclosed within triple backticks.
    """
    header = "=== Final Analysis Result ===\n"
    separator = "=" * 30 + "\n"

    # Use textwrap to wrap the text to 80 characters per line, preserving existing line breaks
    wrapped_lines = []
    for line in text.split('\n'):
        if line.strip().startswith('```python'):
            # Preserve code blocks without wrapping
            wrapped_lines.append(line)
            continue
        wrapped_line = textwrap.fill(line, width=80)
        wrapped_lines.append(wrapped_line)
    wrapped_text = '\n'.join(wrapped_lines)

    # Since the AI response may already contain Markdown formatting, we'll retain it.
    formatted_output = f"{header}\n{wrapped_text}\n{separator}"
    return formatted_output

def main():
    while True:
        prompt = input("Enter a prompt (or type 'exit' to quit): ")
        if prompt.lower() == 'exit':
            print("Exiting the program. Goodbye!")
            break

        # Start timer
        start_time = time.time()

        # Step 1: Generate Initial Response
        initial_response = get_response(prompt)

        if not initial_response:
            print("Failed to generate initial response. Please try again.\n")
            continue

        # Print Initial Response
        print("=== Initial Response ===")
        print(initial_response)
        print("========================\n")

        # Step 2: Think about the initial response
        think_response = think(initial_response)

        if not think_response:
            print("Failed during thinking step. Please try again.\n")
            continue

        # Print Think Response
        print("=== Think Response ===")
        print(think_response)
        print("======================\n")

        # Step 3: Process the thinking response
        process_response = process(think_response)

        if not process_response:
            print("Failed during processing step. Please try again.\n")
            continue

        # Print Process Response
        print("=== Process Response ===")
        print(process_response)
        print("========================\n")

        # Step 4: Analyze the processing response
        analyze_response = analyze(process_response)

        if not analyze_response:
            print("Failed during analyzing step. Please try again.\n")
            continue

        # Print Analyze Response
        print("=== Analyze Response ===")
        print(analyze_response)
        print("========================\n")

        # End timer
        end_time = time.time()
        total_time = end_time - start_time

        # Format the final output nicely
        final_output = format_final_output(analyze_response)
        print(final_output)

        # Display total processing time
        print(f"Total Processing Time: {total_time:.2f} seconds\n")

if __name__ == "__main__":
    main()
