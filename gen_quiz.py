import json
from utilities import load_json

from tutor_llm import generate_toschema






#foreach lesson in topic, if all are complete, quiz time

#number of questions? 4 questions per lesson what ever that ends up being

#foreach lesson in topic.lessons 
#    generate_questions_and_answers(4,lesson.content)

# "question1": "What is the primary purpose of Inference in AI systems?",
#     "question1_correct_answer": "To make predictions or draw conclusions about future events, behaviors, or characteristics.",
#     "question1_incorrect_answer_1": "To analyze patterns and relationships in raw input data",
#     "question1_incorrect_answer_2": "To optimize machine learning algorithms",
#     "question1_incorrect_answer_3

def gen_questions_for_lesson(lesson):
    prompt = f"""You are generating a multi choice quiz.
    All quiz questions should be based on {lesson.content}

    Generate four questions and for each one provide a correct answer and
    three incorrect answers.
"""
    schema = load_json("./schemas/quiz.json")
    quiz_json = json.loads(generate_toschema(prompt, schema))

    with open ("./quiz_output.json","w", encoding="utf-8") as file:
        json.dump(
            quiz_json, 
            file, 
            indent=4,
            )

