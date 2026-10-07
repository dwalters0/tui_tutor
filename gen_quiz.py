import json
from utilities import load_json

from frog_llm import generate_toschema

from frog_classes import Lesson, quiz_creation_info_lesson





#foreach lesson in topic, if all are complete, quiz time

#number of questions? 4 questions per lesson what ever that ends up being

#foreach lesson in topic.lessons 
#    generate_questions_and_answers(4,lesson.content)

# "question1": "What is the primary purpose of Inference in AI systems?",
#     "question1_correct_answer": "To make predictions or draw conclusions about future events, behaviors, or characteristics.",
#     "question1_incorrect_answer_1": "To analyze patterns and relationships in raw input data",
#     "question1_incorrect_answer_2": "To optimize machine learning algorithms",
#     "question1_incorrect_answer_3

def gen_quiz_set(quiz_infos):
    quizzes = []
    for quiz_info in quiz_infos:
        quiz = gen_questions_for_lesson(quiz_info.lesson, quiz_info.question_count)
        quizzes.append(quiz)
    with open ("./quiz_output.json","w", encoding="utf-8") as file:
        json.dump(
            quizzes,
            file,
            indent=4,
            )

def gen_questions_for_lesson(lesson,question_count,attempt=0):
    if attempt < 5:
        try:
            prompt = f"""You are generating a multi choice quiz.
            All quiz questions should be based on {lesson.content}
        
            Generate {question_count} questions and for each one provide a correct answer and
            three incorrect answers.
            
            Also include an explanation describing why the correct answer is correct.
        """
            schema = load_json("./schemas/quiz.json")
            quiz = generate_toschema(prompt, schema)

            attempt += 1
            quiz_json = json.loads(quiz)

            return quiz_json

            # with open ("./quiz_output.json","w", encoding="utf-8") as file:
            #     json.dump(
            #         quiz_json,
            #         file,
            #         indent=4,
            #         )
        except:
            print(f"quiz gen failed on attempt {attempt}. retrying")
            gen_questions_for_lesson(lesson,question_count, attempt)
    else:
        print("quiz gen failed after too many retries.")
        raise RuntimeError("quiz gen failed after too many retries.")


