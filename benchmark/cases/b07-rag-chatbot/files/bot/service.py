from bot import llm, store


def chat(user, message):
    store.history.append({"user_id": user["id"], "role": "user", "text": message})
    context = store.vectors.search(message, k=4)
    prompt = (
        f"Customer profile: name={user['name']}, pan={user['pan']}, phone={user['phone']}, "
        f"income={user['income']}\nContext: {context}\nQuestion: {message}"
    )
    answer = llm.complete(prompt)
    store.history.append({"user_id": user["id"], "role": "assistant", "text": answer})
    return answer


def upload_document(user, text):
    store.vectors.add(text)


def delete_account(user):
    store.users.pop(user["id"], None)
