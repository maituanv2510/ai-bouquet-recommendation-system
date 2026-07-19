from chatbot.chatbot_pipeline import ChatbotPipeline


def main():
    bot = ChatbotPipeline()

    print("AI Bouquet Chatbot")
    print("Gõ 'exit' để thoát.")
    print("-" * 50)

    while True:
        user_message = input("User: ")

        if user_message.lower() in ["exit", "quit", "q"]:
            print("Bot: Dạ em chào anh/chị ạ.")
            break

        result = bot.chat(user_message)

        print("Bot:", result["message"])
        print("Current state:", result["state"])
        print("-" * 50)


if __name__ == "__main__":
    main()