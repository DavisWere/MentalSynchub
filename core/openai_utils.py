import openai
import requests
def generate_chat_completion(user_input, request_info):
    openai.api_key = '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'

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": user_input},
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "assistant", "content": "The following is a conversation with the user:"},
            {"role": "assistant", "content": f"{request_info['method']} request to {request_info['path']} with User-Agent: {request_info['user_agent']}. User says: {user_input}"},
        ],
        temperature=0.7
    )

    return response.choices[0].message['content']